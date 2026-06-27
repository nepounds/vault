"""Tests for Vault duplicate detection API routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.controls.models import ControlFlag
from vault.controls.severities import ControlFlagSeverity
from vault.controls.types import ControlFlagType
from vault.documents.models import Document
from vault.documents.service import create_document_fact, create_document_metadata
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

DUPLICATE_SHA256_HASH = "a" * 64
UNIQUE_SHA256_HASH = "b" * 64
SECOND_UNIQUE_SHA256_HASH = "c" * 64
OTHER_SHA256_HASH = "d" * 64
SAFE_FLAG_KEYS = {
    "id",
    "document_id",
    "flag_type",
    "severity",
    "reason",
    "created_at",
}


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for duplicate route tests."""
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
    """Create a test user for duplicate detection API tests."""
    user = create_user(
        session,
        email=email,
        raw_password="safe password",
        full_name=full_name,
    )
    user.is_active = is_active
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
    organization_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID,
    original_filename: str,
    stored_filename: str,
    sha256_hash: str,
) -> Document:
    """Create document metadata for duplicate detection API tests."""
    return create_document_metadata(
        session,
        organization_id=organization_id,
        uploaded_by_user_id=uploaded_by_user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=sha256_hash,
    )


@pytest.fixture
def duplicate_setup(db_session: Session) -> dict[str, object]:
    """Create users, organizations, documents, and duplicate facts."""
    owner = create_api_user(
        db_session,
        email="duplicate-owner@example.com",
        full_name="Duplicate Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="duplicate-reviewer@example.com",
        full_name="Duplicate Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="duplicate-viewer@example.com",
        full_name="Duplicate Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="duplicate-outsider@example.com",
        full_name="Duplicate Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="duplicate-inactive@example.com",
        full_name="Duplicate Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Duplicate Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Duplicate Company",
    )
    add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )
    add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )
    target_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="target.pdf",
        stored_filename="generated-target.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    duplicate_hash_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="same-hash.pdf",
        stored_filename="generated-same-hash.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    duplicate_invoice_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="same-invoice.pdf",
        stored_filename="generated-same-invoice.pdf",
        sha256_hash=UNIQUE_SHA256_HASH,
    )
    clean_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="clean.pdf",
        stored_filename="generated-clean.pdf",
        sha256_hash=SECOND_UNIQUE_SHA256_HASH,
    )
    other_document = create_api_document(
        db_session,
        organization_id=other_created.organization.id,
        uploaded_by_user_id=outsider.id,
        original_filename="other.pdf",
        stored_filename="generated-other.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    create_document_fact(
        db_session,
        document_id=target_document.id,
        vendor_name="Shared Vendor",
        invoice_number="INV-100",
        invoice_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15),
        amount_cents=12_345,
        currency="USD",
        category="Office Supplies",
    )
    create_document_fact(
        db_session,
        document_id=duplicate_invoice_document.id,
        vendor_name="shared vendor",
        invoice_number="INV-100",
        invoice_date=date(2026, 1, 16),
        due_date=date(2026, 2, 16),
        amount_cents=12_345,
        currency="USD",
        category="Office Supplies",
    )
    create_document_fact(
        db_session,
        document_id=other_document.id,
        vendor_name="Shared Vendor",
        invoice_number="INV-100",
        invoice_date=date(2026, 1, 17),
        due_date=date(2026, 2, 17),
        amount_cents=12_345,
        currency="USD",
        category="Office Supplies",
    )
    create_document_fact(
        db_session,
        document_id=clean_document.id,
        vendor_name="Clean Vendor",
        invoice_number="INV-200",
        invoice_date=date(2026, 1, 18),
        due_date=date(2026, 2, 18),
        amount_cents=99_999,
        currency="USD",
        category="Meals",
    )
    db_session.commit()
    return {
        "organization_id": created.organization.id,
        "other_organization_id": other_created.organization.id,
        "owner": owner,
        "reviewer": reviewer,
        "viewer": viewer,
        "outsider": outsider,
        "inactive_user": inactive_user,
        "target_document": target_document,
        "duplicate_hash_document": duplicate_hash_document,
        "duplicate_invoice_document": duplicate_invoice_document,
        "clean_document": clean_document,
        "other_document": other_document,
    }


def token_for(setup: dict[str, object], key: str) -> str:
    user = setup[key]
    assert isinstance(user, User)
    return create_access_token(user.id)


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def other_organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["other_organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def document_id_from(
    setup: dict[str, object],
    key: str = "target_document",
) -> uuid.UUID:
    document = setup[key]
    assert isinstance(document, Document)
    return document.id


def generate_url(organization_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return (
        f"/organizations/{organization_id}/documents/{document_id}"
        "/duplicates/generate"
    )


def generate_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    document_key: str = "target_document",
) -> Response:
    response: Response = client.post(
        generate_url(
            organization_id_from(setup),
            document_id_from(setup, document_key),
        ),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def assert_safe_flag_payload(payload: dict[str, object]) -> None:
    assert set(payload) == SAFE_FLAG_KEYS
    assert "stored_path" not in payload
    assert "stored_filename" not in payload
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "access_token" not in payload


def generated_flag_rows(
    session: Session,
    *,
    document_id: uuid.UUID,
) -> list[ControlFlag]:
    statement = select(ControlFlag).where(ControlFlag.document_id == document_id)
    return list(session.scalars(statement))


def generated_payload_types(response: Response) -> set[str]:
    return {item["flag_type"] for item in response.json()}


def test_owner_can_generate_duplicate_flags(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    assert response.json()


def test_reviewer_can_generate_duplicate_flags(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "reviewer")

    assert response.status_code == 200
    assert response.json()


def test_viewer_cannot_generate_duplicate_flags(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "viewer")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_non_member_cannot_generate_duplicate_flags(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_token_returns_unauthorized_for_duplicate_generation(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup),
        ),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized_for_duplicate_generation(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup),
        ),
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized_for_duplicate_generation(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    owner = duplicate_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    response: Response = client.post(
        generate_url(
            organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup),
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_unknown_user_token_returns_unauthorized_for_duplicate_generation(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup),
        ),
        headers=auth_headers(create_access_token(uuid.uuid4())),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_returns_unauthorized_for_duplicate_generation(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "inactive_user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_unknown_organization_returns_safe_forbidden_behavior(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(uuid.uuid4(), document_id_from(duplicate_setup)),
        headers=auth_headers(token_for(duplicate_setup, "owner")),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_generation_verifies_document_belongs_to_path_organization(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            other_organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup),
        ),
        headers=auth_headers(token_for(duplicate_setup, "outsider")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_generation_rejects_document_from_another_organization(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            organization_id_from(duplicate_setup),
            document_id_from(duplicate_setup, "other_document"),
        ),
        headers=auth_headers(token_for(duplicate_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_missing_document_in_accessible_organization_returns_not_found(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(organization_id_from(duplicate_setup), uuid.uuid4()),
        headers=auth_headers(token_for(duplicate_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_duplicate_file_hash_generation_returns_duplicate_file_hash_flag(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    assert ControlFlagType.DUPLICATE_FILE_HASH.value in generated_payload_types(
        response,
    )


def test_duplicate_invoice_generation_returns_duplicate_invoice_flag(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    assert ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value in (
        generated_payload_types(response)
    )


def test_duplicate_file_hash_flag_severity_is_blocker(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")
    severities = {
        item["flag_type"]: item["severity"]
        for item in response.json()
    }

    assert severities[ControlFlagType.DUPLICATE_FILE_HASH.value] == (
        ControlFlagSeverity.BLOCKER.value
    )


def test_duplicate_invoice_flag_severity_is_warning(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")
    severities = {
        item["flag_type"]: item["severity"]
        for item in response.json()
    }

    assert severities[ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value] == (
        ControlFlagSeverity.WARNING.value
    )


def test_generation_persists_generated_control_flag_rows(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)
    rows = generated_flag_rows(db_session, document_id=document_id)

    assert response.status_code == 200
    assert len(rows) == 2


def test_generated_rows_store_document_id(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)

    assert all(
        flag.document_id == document_id
        for flag in generated_flag_rows(db_session, document_id=document_id)
    )


def test_generated_rows_store_official_flag_type_values(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)
    flag_types = {
        flag.flag_type
        for flag in generated_flag_rows(db_session, document_id=document_id)
    }

    assert flag_types == {
        ControlFlagType.DUPLICATE_FILE_HASH.value,
        ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value,
    }


def test_generated_rows_store_official_severity_values(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)
    severities = {
        flag.severity
        for flag in generated_flag_rows(db_session, document_id=document_id)
    }

    assert severities == {
        ControlFlagSeverity.BLOCKER.value,
        ControlFlagSeverity.WARNING.value,
    }


def test_generated_rows_store_safe_non_blank_reasons(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)
    reasons = [
        flag.reason
        for flag in generated_flag_rows(db_session, document_id=document_id)
    ]

    assert all(reasons)
    assert all("generated-" not in reason for reason in reasons)
    assert all("/tmp/" not in reason for reason in reasons)
    assert all("C:\\" not in reason for reason in reasons)


def test_generated_rows_have_ids(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)

    assert all(
        flag.id
        for flag in generated_flag_rows(db_session, document_id=document_id)
    )


def test_generated_rows_have_created_timestamps(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    generate_as(client, duplicate_setup, "owner")
    document_id = document_id_from(duplicate_setup)

    assert all(
        flag.created_at
        for flag in generated_flag_rows(db_session, document_id=document_id)
    )


def test_generation_returns_empty_list_when_no_duplicate_flags_are_generated(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner", "clean_document")

    assert response.status_code == 200
    assert response.json() == []


def test_generation_does_not_flag_cross_organization_duplicate_file_hashes(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    duplicate_hash_document = duplicate_setup["duplicate_hash_document"]
    assert isinstance(duplicate_hash_document, Document)
    db_session.delete(duplicate_hash_document)
    db_session.commit()

    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    assert ControlFlagType.DUPLICATE_FILE_HASH.value not in generated_payload_types(
        response,
    )


def test_generation_does_not_flag_cross_organization_duplicate_invoice_facts(
    client: TestClient,
    db_session: Session,
    duplicate_setup: dict[str, object],
) -> None:
    duplicate_invoice_document = duplicate_setup["duplicate_invoice_document"]
    assert isinstance(duplicate_invoice_document, Document)
    db_session.delete(duplicate_invoice_document)
    db_session.commit()

    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    assert ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value not in (
        generated_payload_types(response)
    )


def test_duplicate_responses_return_safe_metadata(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    for item in response.json():
        assert_safe_flag_payload(item)
        assert item["document_id"] == str(document_id_from(duplicate_setup))


def test_duplicate_responses_do_not_include_local_absolute_paths(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")
    serialized = response.text

    assert "stored_path" not in serialized
    assert "generated-" not in serialized
    assert "/tmp/" not in serialized
    assert "C:\\" not in serialized


def test_duplicate_responses_do_not_include_raw_passwords(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert "safe password" not in response.text
    assert "password" not in response.text


def test_duplicate_responses_do_not_include_password_hashes(
    client: TestClient,
    duplicate_setup: dict[str, object],
) -> None:
    response = generate_as(client, duplicate_setup, "owner")

    assert "password_hash" not in response.text
    assert "$argon2" not in response.text


def test_duplicate_route_appears_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]
    generate_path = (
        "/organizations/{organization_id}/documents/{document_id}"
        "/duplicates/generate"
    )

    assert generate_path in paths


def test_duplicate_generation_creates_audit_entry(
    client: TestClient,
    duplicate_setup: dict[str, object],
    db_session: Session,
) -> None:
    owner = duplicate_setup["owner"]
    assert isinstance(owner, User)

    response = generate_as(client, duplicate_setup, "owner")

    assert response.status_code == 200
    generated_flags = response.json()
    audit_entry = db_session.scalars(select(AuditEntry)).all()[-1]
    assert audit_entry.action == AuditAction.DUPLICATE_FLAGS_GENERATED.value
    assert audit_entry.entity_type == AuditEntityType.DOCUMENT.value
    assert str(audit_entry.entity_id) == str(document_id_from(duplicate_setup))
    assert str(audit_entry.organization_id) == str(
        organization_id_from(duplicate_setup)
    )
    assert audit_entry.actor_user_id == owner.id
    generated_flag_metadata = audit_entry.metadata_json["generated_flags"]
    assert isinstance(generated_flag_metadata, list)
    assert audit_entry.metadata_json["generated_flag_count"] == len(generated_flags)
    assert len(generated_flag_metadata) == len(generated_flags)


def test_duplicate_generation_zero_flags_still_creates_audit_entry(
    client: TestClient,
    duplicate_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = generate_as(client, duplicate_setup, "owner", "clean_document")

    assert response.status_code == 200
    assert response.json() == []
    audit_entry = db_session.scalars(select(AuditEntry)).all()[-1]
    assert audit_entry.action == AuditAction.DUPLICATE_FLAGS_GENERATED.value
    assert audit_entry.metadata_json["generated_flag_count"] == 0
    assert audit_entry.metadata_json["generated_flags"] == []


def test_viewer_denied_duplicate_generation_does_not_create_audit_entry(
    client: TestClient,
    duplicate_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = generate_as(client, duplicate_setup, "viewer")

    assert response.status_code == 403
    assert db_session.scalars(select(AuditEntry)).all() == []
