"""Tests for Vault CSV export API routes."""

from __future__ import annotations

import builtins
import csv
import io
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.audit.service import create_audit_entry
from vault.auth.models import User
from vault.auth.tokens import create_access_token
from vault.controls.service import create_control_flag
from vault.controls.severities import ControlFlagSeverity
from vault.controls.types import ControlFlagType
from vault.documents.models import Document
from vault.documents.service import create_document_fact, create_document_metadata
from vault.documents.statuses import DocumentStatus
from vault.exports.builders import (
    APPROVED_DOCUMENTS_HEADERS,
    AUDIT_LOG_HEADERS,
    EXCEPTIONS_REPORT_HEADERS,
)
from vault.models import Base
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64
APPROVED_EXPORT_PATH = "/organizations/{organization_id}/exports/approved-documents"
EXCEPTIONS_EXPORT_PATH = "/organizations/{organization_id}/exports/exceptions-report"
AUDIT_LOG_EXPORT_PATH = "/organizations/{organization_id}/exports/audit-log"
SENSITIVE_RESPONSE_FRAGMENTS = (
    "raw-secret-password",
    "fake-test-password-hash",
    "argon2id",
    "Bearer ",
    "/home/nathan/vault/uploads/private.pdf",
    "C:\\Users\\Nathan\\vault\\uploads\\private.pdf",
)


@dataclass(frozen=True)
class ExportApiSetup:
    """Database records used by export route tests."""

    owner: User
    reviewer: User
    viewer: User
    outsider: User
    inactive_user: User
    organization: Organization
    other_organization: Organization
    approved_document: Document
    flagged_document: Document
    audit_entry: AuditEntry
    other_org_document: Document


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for export route tests."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Open a database session for arranging and inspecting API effects."""
    with session_factory() as test_session:
        yield test_session


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Create a test client with a dependency-overridden database session."""
    app = create_app()

    def override_database_session() -> Iterator[Session]:
        with session_factory() as test_session:
            yield test_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_api_user(
    session: Session,
    *,
    email: str,
    full_name: str,
    is_active: bool = True,
) -> User:
    """Create a test user without needing password verification behavior."""
    user = User()
    user.email = email
    user.password_hash = "fake-test-password-hash"
    user.full_name = full_name
    user.is_active = is_active
    session.add(user)
    session.flush()
    return user


def add_membership(
    session: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MembershipRole,
) -> Membership:
    """Add an organization membership with an official role."""
    membership = Membership()
    membership.organization_id = organization_id
    membership.user_id = user_id
    membership.role = role.value
    session.add(membership)
    session.flush()
    return membership


def create_api_document(
    session: Session,
    *,
    organization: Organization,
    user: User,
    filename: str,
    status_value: str,
    hash_character: str,
) -> Document:
    """Create a document record for export API tests."""
    document = create_document_metadata(
        session,
        organization_id=organization.id,
        uploaded_by_user_id=user.id,
        original_filename=filename,
        stored_filename=f"{hash_character}-generated.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=hash_character * len(VALID_SHA256_HASH),
    )
    document.status = status_value
    session.flush()
    return document


def read_csv(text: str) -> list[dict[str, str]]:
    """Read CSV text into dictionaries for assertions."""
    return list(csv.DictReader(io.StringIO(text)))


def auth_headers(user: User) -> dict[str, str]:
    """Return an Authorization header for a user."""
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def expired_auth_headers(user: User) -> dict[str, str]:
    """Return an Authorization header with an expired token."""
    token = create_access_token(user.id, expires_delta=timedelta(minutes=-1))
    return {"Authorization": f"Bearer {token}"}


def export_url(path_template: str, organization_id: uuid.UUID) -> str:
    """Format an export route path for one organization."""
    return path_template.format(organization_id=organization_id)


def get_export(
    client: TestClient,
    *,
    path_template: str,
    organization_id: uuid.UUID,
    user: User,
) -> Response:
    """Call one export route as a specific user."""
    response = client.get(
        export_url(path_template, organization_id),
        headers=auth_headers(user),
    )
    return Response(
        status_code=response.status_code,
        headers=response.headers,
        content=response.content,
        request=response.request,
    )


def count_export_audit_entries(
    session: Session,
    *,
    organization_id: uuid.UUID | None = None,
) -> int:
    """Count export-generated audit entries, optionally by organization."""
    filters = [AuditEntry.action == AuditAction.EXPORT_GENERATED.value]
    if organization_id is not None:
        filters.append(AuditEntry.organization_id == organization_id)
    statement = select(func.count()).select_from(AuditEntry).where(*filters)
    return session.scalar(statement) or 0


@pytest.fixture
def export_setup(db_session: Session) -> ExportApiSetup:
    """Create users, organizations, memberships, and exportable records."""
    owner = create_api_user(
        db_session,
        email="export-owner@example.com",
        full_name="Export Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="export-reviewer@example.com",
        full_name="Export Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="export-viewer@example.com",
        full_name="Export Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="export-outsider@example.com",
        full_name="Export Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="export-inactive@example.com",
        full_name="Export Inactive",
        is_active=False,
    )
    created = create_organization(db_session, creator=owner, name="Export Co")
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Export Co",
    )
    organization = created.organization
    other_organization = other_created.organization
    add_membership(
        db_session,
        organization_id=organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )
    add_membership(
        db_session,
        organization_id=organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )
    approved_document = create_api_document(
        db_session,
        organization=organization,
        user=owner,
        filename="approved.pdf",
        status_value=DocumentStatus.APPROVED.value,
        hash_character="a",
    )
    create_document_fact(
        db_session,
        document_id=approved_document.id,
        vendor_name="Approved Vendor",
        invoice_number="INV-100",
        invoice_date=date(2026, 1, 10),
        due_date=date(2026, 2, 10),
        amount_cents=12345,
        currency="USD",
        category="Office Supplies",
        memo="Approved memo",
    )
    for status_value, hash_character in (
        (DocumentStatus.PENDING.value, "b"),
        (DocumentStatus.REJECTED.value, "c"),
        (DocumentStatus.NEEDS_INFO.value, "d"),
    ):
        create_api_document(
            db_session,
            organization=organization,
            user=owner,
            filename=f"{status_value}.pdf",
            status_value=status_value,
            hash_character=hash_character,
        )
    flagged_document = create_api_document(
        db_session,
        organization=organization,
        user=owner,
        filename="flagged.pdf",
        status_value=DocumentStatus.PENDING.value,
        hash_character="e",
    )
    create_control_flag(
        db_session,
        document_id=flagged_document.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="High amount.",
    )
    audit_entry = create_audit_entry(
        db_session,
        organization_id=organization.id,
        actor_user_id=owner.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=approved_document.id,
        summary="Document uploaded.",
        metadata_json={
            "safe_value": "kept",
            "raw_password": "raw-secret-password",
            "token_payload": {"sub": "private-user-id"},
            "stored_path": "/home/nathan/vault/uploads/private.pdf",
            "windows_path": "C:\\Users\\Nathan\\vault\\uploads\\private.pdf",
        },
    )
    other_org_document = create_api_document(
        db_session,
        organization=other_organization,
        user=outsider,
        filename="other-approved.pdf",
        status_value=DocumentStatus.APPROVED.value,
        hash_character="f",
    )
    other_flagged_document = create_api_document(
        db_session,
        organization=other_organization,
        user=outsider,
        filename="other-flagged.pdf",
        status_value=DocumentStatus.PENDING.value,
        hash_character="0",
    )
    create_control_flag(
        db_session,
        document_id=other_flagged_document.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="Other high amount.",
    )
    create_audit_entry(
        db_session,
        organization_id=other_organization.id,
        actor_user_id=outsider.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=other_org_document.id,
        summary="Other document uploaded.",
    )
    create_audit_entry(
        db_session,
        organization_id=None,
        actor_user_id=owner.id,
        action=AuditAction.USER_REGISTERED.value,
        entity_type=AuditEntityType.USER.value,
        entity_id=owner.id,
        summary="Organization-null entry.",
    )
    db_session.commit()
    return ExportApiSetup(
        owner=owner,
        reviewer=reviewer,
        viewer=viewer,
        outsider=outsider,
        inactive_user=inactive_user,
        organization=organization,
        other_organization=other_organization,
        approved_document=approved_document,
        flagged_document=flagged_document,
        audit_entry=audit_entry,
        other_org_document=other_org_document,
    )


@pytest.mark.parametrize("user_attr", ["owner", "reviewer"])
def test_owner_and_reviewer_can_download_approved_documents_csv(
    client: TestClient,
    export_setup: ExportApiSetup,
    user_attr: str,
) -> None:
    user = getattr(export_setup, user_attr)
    assert isinstance(user, User)

    response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=user,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="approved_documents.csv"' in response.headers[
        "content-disposition"
    ]
    assert response.text.startswith(",".join(APPROVED_DOCUMENTS_HEADERS))


def test_viewer_and_non_member_cannot_download_approved_documents_csv(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    before_count = count_export_audit_entries(db_session)

    viewer_response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.viewer,
    )
    outsider_response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.outsider,
    )

    assert viewer_response.status_code == 403
    assert outsider_response.status_code == 403
    assert count_export_audit_entries(db_session) == before_count


def test_approved_documents_export_authentication_failures(
    client: TestClient,
    export_setup: ExportApiSetup,
) -> None:
    url = export_url(APPROVED_EXPORT_PATH, export_setup.organization.id)

    missing = client.get(url)
    invalid = client.get(url, headers={"Authorization": "Bearer not-a-token"})
    expired = client.get(url, headers=expired_auth_headers(export_setup.owner))
    inactive = client.get(url, headers=auth_headers(export_setup.inactive_user))

    assert missing.status_code == 401
    assert invalid.status_code == 401
    assert expired.status_code == 401
    assert inactive.status_code == 401


@pytest.mark.parametrize(
    "path_template",
    [APPROVED_EXPORT_PATH, EXCEPTIONS_EXPORT_PATH, AUDIT_LOG_EXPORT_PATH],
)
def test_unknown_organization_returns_safe_403_for_export_routes(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
    path_template: str,
) -> None:
    before_count = count_export_audit_entries(db_session)

    response = get_export(
        client,
        path_template=path_template,
        organization_id=uuid.uuid4(),
        user=export_setup.owner,
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Organization access is not available."}
    assert count_export_audit_entries(db_session) == before_count


def test_approved_documents_export_scopes_rows_and_includes_fact_fields(
    client: TestClient,
    export_setup: ExportApiSetup,
) -> None:
    response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.owner,
    )
    records = read_csv(response.text)

    assert response.status_code == 200
    assert len(records) == 1
    assert records[0]["document_id"] == str(export_setup.approved_document.id)
    assert records[0]["original_filename"] == "approved.pdf"
    assert records[0]["status"] == DocumentStatus.APPROVED.value
    assert records[0]["vendor_name"] == "Approved Vendor"
    assert records[0]["invoice_number"] == "INV-100"
    assert records[0]["amount_cents"] == "12345"
    assert "pending.pdf" not in response.text
    assert "rejected.pdf" not in response.text
    assert "needs_info.pdf" not in response.text
    assert "other-approved.pdf" not in response.text


def test_approved_documents_export_returns_headers_when_empty(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    db_session.execute(
        delete(Document).where(
            Document.organization_id == export_setup.other_organization.id
        )
    )
    db_session.commit()

    response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.other_organization.id,
        user=export_setup.outsider,
    )

    assert response.status_code == 200
    assert response.text.splitlines() == [",".join(APPROVED_DOCUMENTS_HEADERS)]


@pytest.mark.parametrize("user_attr", ["owner", "reviewer"])
def test_owner_and_reviewer_can_download_exceptions_report_csv(
    client: TestClient,
    export_setup: ExportApiSetup,
    user_attr: str,
) -> None:
    user = getattr(export_setup, user_attr)
    assert isinstance(user, User)

    response = get_export(
        client,
        path_template=EXCEPTIONS_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=user,
    )
    records = read_csv(response.text)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="exceptions_report.csv"' in response.headers[
        "content-disposition"
    ]
    assert response.text.startswith(",".join(EXCEPTIONS_REPORT_HEADERS))
    assert len(records) == 1
    assert records[0]["document_id"] == str(export_setup.flagged_document.id)
    assert records[0]["flag_type"] == ControlFlagType.HIGH_AMOUNT.value
    assert records[0]["severity"] == ControlFlagSeverity.BLOCKER.value
    assert "Other high amount" not in response.text


def test_viewer_cannot_download_exceptions_report_csv(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    before_count = count_export_audit_entries(db_session)

    response = get_export(
        client,
        path_template=EXCEPTIONS_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.viewer,
    )

    assert response.status_code == 403
    assert count_export_audit_entries(db_session) == before_count


def test_exceptions_report_export_returns_headers_when_empty(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    db_session.execute(
        delete(AuditEntry).where(
            AuditEntry.organization_id == export_setup.other_organization.id
        )
    )
    db_session.execute(
        delete(Document).where(
            Document.organization_id == export_setup.other_organization.id
        )
    )
    db_session.commit()

    response = get_export(
        client,
        path_template=EXCEPTIONS_EXPORT_PATH,
        organization_id=export_setup.other_organization.id,
        user=export_setup.outsider,
    )

    assert response.status_code == 200
    assert response.text.splitlines() == [",".join(EXCEPTIONS_REPORT_HEADERS)]


@pytest.mark.parametrize("user_attr", ["owner", "reviewer"])
def test_owner_and_reviewer_can_download_audit_log_csv(
    client: TestClient,
    export_setup: ExportApiSetup,
    user_attr: str,
) -> None:
    user = getattr(export_setup, user_attr)
    assert isinstance(user, User)

    response = get_export(
        client,
        path_template=AUDIT_LOG_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=user,
    )
    records = read_csv(response.text)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="audit_log.csv"' in response.headers["content-disposition"]
    assert response.text.startswith(",".join(AUDIT_LOG_HEADERS))
    assert any(
        record["audit_entry_id"] == str(export_setup.audit_entry.id)
        for record in records
    )
    assert "Other document uploaded" not in response.text
    assert "Organization-null entry" not in response.text


def test_viewer_cannot_download_audit_log_csv(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    before_count = count_export_audit_entries(db_session)

    response = get_export(
        client,
        path_template=AUDIT_LOG_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.viewer,
    )

    assert response.status_code == 403
    assert count_export_audit_entries(db_session) == before_count


def test_audit_log_export_returns_headers_when_empty(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
) -> None:
    db_session.execute(
        delete(AuditEntry).where(
            AuditEntry.organization_id == export_setup.other_organization.id
        )
    )
    db_session.commit()

    response = get_export(
        client,
        path_template=AUDIT_LOG_EXPORT_PATH,
        organization_id=export_setup.other_organization.id,
        user=export_setup.outsider,
    )

    assert response.status_code == 200
    assert response.text.splitlines() == [",".join(AUDIT_LOG_HEADERS)]


def test_export_routes_appear_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "/organizations/{organization_id}/exports/approved-documents" in paths
    assert "/organizations/{organization_id}/exports/exceptions-report" in paths
    assert "/organizations/{organization_id}/exports/audit-log" in paths


@pytest.mark.parametrize(
    ("path_template", "export_type", "filename"),
    [
        (APPROVED_EXPORT_PATH, "approved_documents", "approved_documents.csv"),
        (EXCEPTIONS_EXPORT_PATH, "exceptions_report", "exceptions_report.csv"),
        (AUDIT_LOG_EXPORT_PATH, "audit_log", "audit_log.csv"),
    ],
)
def test_each_successful_export_creates_safe_export_generated_audit_entry(
    client: TestClient,
    db_session: Session,
    export_setup: ExportApiSetup,
    path_template: str,
    export_type: str,
    filename: str,
) -> None:
    before_count = count_export_audit_entries(
        db_session,
        organization_id=export_setup.organization.id,
    )

    response = get_export(
        client,
        path_template=path_template,
        organization_id=export_setup.organization.id,
        user=export_setup.owner,
    )

    audit_entries = db_session.scalars(
        select(AuditEntry)
        .where(
            AuditEntry.organization_id == export_setup.organization.id,
            AuditEntry.action == AuditAction.EXPORT_GENERATED.value,
        )
        .order_by(AuditEntry.created_at.desc())
    ).all()
    newest_entry = audit_entries[0]

    assert response.status_code == 200
    assert len(audit_entries) == before_count + 1
    assert newest_entry.actor_user_id == export_setup.owner.id
    assert newest_entry.entity_type == AuditEntityType.EXPORT.value
    assert newest_entry.entity_id is None
    assert newest_entry.metadata_json["export_type"] == export_type
    assert newest_entry.metadata_json["filename"] == filename
    assert isinstance(newest_entry.metadata_json["row_count"], int)
    assert response.text not in str(newest_entry.metadata_json)
    assert "document_id" not in str(newest_entry.metadata_json)


def test_export_responses_do_not_expose_sensitive_values(
    client: TestClient,
    export_setup: ExportApiSetup,
) -> None:
    responses = [
        get_export(
            client,
            path_template=path_template,
            organization_id=export_setup.organization.id,
            user=export_setup.owner,
        )
        for path_template in (
            APPROVED_EXPORT_PATH,
            EXCEPTIONS_EXPORT_PATH,
            AUDIT_LOG_EXPORT_PATH,
        )
    ]
    combined_text = "\n".join(response.text for response in responses)

    for fragment in SENSITIVE_RESPONSE_FRAGMENTS:
        assert fragment not in combined_text


def test_export_routes_do_not_write_files(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
    export_setup: ExportApiSetup,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("export routes must not write files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "write_text", fail_open)
    monkeypatch.setattr(Path, "write_bytes", fail_open)

    response = get_export(
        client,
        path_template=APPROVED_EXPORT_PATH,
        organization_id=export_setup.organization.id,
        user=export_setup.owner,
    )

    assert response.status_code == 200
