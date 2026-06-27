"""Tests for Vault CSV export builders and row queries."""

from __future__ import annotations

import builtins
import csv
import io
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.audit.service import create_audit_entry
from vault.auth.models import User
from vault.auth.service import create_user
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
    build_approved_documents_csv,
    build_audit_log_csv,
    build_exceptions_report_csv,
)
from vault.exports.service import (
    list_approved_document_export_rows,
    list_audit_log_export_rows,
    list_exception_report_export_rows,
)
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64


class CommitTrackingSession(Session):
    """Test session that records unexpected commits."""

    commit_count: int

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.commit_count = 0

    def commit(self) -> None:
        self.commit_count += 1
        super().commit()


@pytest.fixture
def session() -> Iterator[CommitTrackingSession]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        class_=CommitTrackingSession,
        autoflush=False,
        autocommit=False,
    )

    with session_factory() as test_session:
        yield test_session


@pytest.fixture
def user(session: Session) -> User:
    return create_user(
        session,
        email="owner@example.com",
        raw_password="safe password",
        full_name="Owner Example",
    )


@pytest.fixture
def organization(session: Session, user: User) -> Organization:
    return create_organization(
        session,
        creator=user,
        name="Example Company",
    ).organization


def create_other_organization(session: Session) -> tuple[User, Organization]:
    user = create_user(
        session,
        email="other@example.com",
        raw_password="safe password",
        full_name="Other Owner",
    )
    organization = create_organization(
        session,
        creator=user,
        name="Other Company",
    ).organization

    return user, organization


def create_document(
    session: Session,
    *,
    organization: Organization,
    user: User,
    filename: str,
    status: str = DocumentStatus.PENDING.value,
    hash_character: str = "a",
    created_at: datetime | None = None,
) -> Document:
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
    document.status = status
    if created_at is not None:
        document.created_at = created_at
    session.flush()

    return document


def read_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


def count_audit_entries(session: Session) -> int:
    return session.scalar(select(func.count()).select_from(AuditEntry)) or 0


def test_approved_documents_export_returns_csv_text_and_stable_headers(
    session: Session,
) -> None:
    rows = list_approved_document_export_rows(
        session,
        organization_id=object_id(),
    )
    csv_text = build_approved_documents_csv(rows)

    assert isinstance(csv_text, str)
    assert csv_text.splitlines() == [",".join(APPROVED_DOCUMENTS_HEADERS)]


def test_approved_documents_export_filters_statuses_and_organization(
    session: Session,
    organization: Organization,
    user: User,
) -> None:
    approved = create_document(
        session,
        organization=organization,
        user=user,
        filename='approved, "invoice".pdf',
        status=DocumentStatus.APPROVED.value,
        hash_character="a",
    )
    create_document_fact(
        session,
        document_id=approved.id,
        vendor_name='Vendor, "A"',
        invoice_number='INV, "100"',
        invoice_date=date(2026, 1, 10),
        due_date=date(2026, 2, 10),
        amount_cents=12345,
        currency="USD",
        category="Office Supplies",
        memo="Line one\nLine two",
    )
    create_document(
        session,
        organization=organization,
        user=user,
        filename="pending.pdf",
        status=DocumentStatus.PENDING.value,
        hash_character="b",
    )
    create_document(
        session,
        organization=organization,
        user=user,
        filename="rejected.pdf",
        status=DocumentStatus.REJECTED.value,
        hash_character="c",
    )
    create_document(
        session,
        organization=organization,
        user=user,
        filename="needs-info.pdf",
        status=DocumentStatus.NEEDS_INFO.value,
        hash_character="d",
    )
    other_user, other_org = create_other_organization(session)
    create_document(
        session,
        organization=other_org,
        user=other_user,
        filename="other-approved.pdf",
        status=DocumentStatus.APPROVED.value,
        hash_character="e",
    )

    rows = list_approved_document_export_rows(
        session,
        organization_id=organization.id,
    )
    records = read_csv(build_approved_documents_csv(rows))

    assert len(records) == 1
    assert records[0]["document_id"] == str(approved.id)
    assert records[0]["original_filename"] == 'approved, "invoice".pdf'
    assert records[0]["status"] == DocumentStatus.APPROVED.value
    assert records[0]["vendor_name"] == 'Vendor, "A"'
    assert records[0]["invoice_number"] == 'INV, "100"'
    assert records[0]["invoice_date"] == "2026-01-10"
    assert records[0]["due_date"] == "2026-02-10"
    assert records[0]["amount_cents"] == "12345"
    assert records[0]["currency"] == "USD"
    assert records[0]["category"] == "Office Supplies"
    assert records[0]["memo"] == "Line one\nLine two"
    assert "other-approved" not in build_approved_documents_csv(rows)


def test_approved_documents_export_includes_blank_fact_fields(
    session: Session,
    organization: Organization,
    user: User,
) -> None:
    document = create_document(
        session,
        organization=organization,
        user=user,
        filename="approved-no-facts.pdf",
        status=DocumentStatus.APPROVED.value,
    )

    rows = list_approved_document_export_rows(
        session,
        organization_id=organization.id,
    )
    records = read_csv(build_approved_documents_csv(rows))

    assert records[0]["document_id"] == str(document.id)
    assert records[0]["vendor_name"] == ""
    assert records[0]["invoice_number"] == ""
    assert records[0]["amount_cents"] == ""


def test_exception_report_export_includes_flags_and_orders_by_severity(
    session: Session,
    organization: Organization,
    user: User,
) -> None:
    document = create_document(
        session,
        organization=organization,
        user=user,
        filename='flagged, "invoice".pdf',
        status=DocumentStatus.NEEDS_INFO.value,
    )
    info = create_control_flag(
        session,
        document_id=document.id,
        flag_type=ControlFlagType.MISSING_DUE_DATE.value,
        severity=ControlFlagSeverity.INFO.value,
        reason='Info, "quoted" reason',
    )
    warning = create_control_flag(
        session,
        document_id=document.id,
        flag_type=ControlFlagType.MISSING_INVOICE_DATE.value,
        severity=ControlFlagSeverity.WARNING.value,
        reason="Warning reason",
    )
    blocker = create_control_flag(
        session,
        document_id=document.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="Blocker reason",
    )
    other_user, other_org = create_other_organization(session)
    other_doc = create_document(
        session,
        organization=other_org,
        user=other_user,
        filename="other-flagged.pdf",
        status=DocumentStatus.APPROVED.value,
        hash_character="b",
    )
    create_control_flag(
        session,
        document_id=other_doc.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="Other org reason",
    )

    rows = list_exception_report_export_rows(
        session,
        organization_id=organization.id,
    )
    csv_text = build_exceptions_report_csv(rows)
    records = read_csv(csv_text)

    assert csv_text.startswith(",".join(EXCEPTIONS_REPORT_HEADERS))
    assert [record["flag_id"] for record in records] == [
        str(blocker.id),
        str(warning.id),
        str(info.id),
    ]
    assert records[0]["document_id"] == str(document.id)
    assert records[0]["original_filename"] == 'flagged, "invoice".pdf'
    assert records[0]["document_status"] == DocumentStatus.NEEDS_INFO.value
    assert records[0]["flag_type"] == ControlFlagType.HIGH_AMOUNT.value
    assert records[0]["severity"] == ControlFlagSeverity.BLOCKER.value
    assert records[2]["reason"] == 'Info, "quoted" reason'
    assert "other-flagged" not in csv_text


def test_exception_report_empty_export_returns_headers_only(session: Session) -> None:
    rows = list_exception_report_export_rows(
        session,
        organization_id=object_id(),
    )

    assert build_exceptions_report_csv(rows).splitlines() == [
        ",".join(EXCEPTIONS_REPORT_HEADERS)
    ]


def test_audit_log_export_includes_safe_metadata_and_scopes_organization(
    session: Session,
    organization: Organization,
    user: User,
) -> None:
    create_audit_entry(
        session,
        organization_id=organization.id,
        actor_user_id=user.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=object_id(),
        summary='Uploaded, "document".',
        metadata_json={
            "safe_value": "kept",
            "raw_password": "secret",
            "password_hash": "argon2 hash",
            "authorization": "Bearer abc.def.ghi",
            "token_payload": {"sub": "user-id"},
            "stored_path": "/tmp/private/upload.pdf",
            "nested": {"access_token": "eyJ.fake.token"},
            "list_values": ["Bearer list.token.value"],
            "b_value": "second",
            "a_value": "first",
        },
    )
    other_user, other_org = create_other_organization(session)
    create_audit_entry(
        session,
        organization_id=other_org.id,
        actor_user_id=other_user.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        summary="Other organization entry.",
    )
    create_audit_entry(
        session,
        organization_id=None,
        actor_user_id=user.id,
        action=AuditAction.USER_REGISTERED.value,
        entity_type=AuditEntityType.USER.value,
        summary="Organization-null entry.",
    )

    rows = list_audit_log_export_rows(session, organization_id=organization.id)
    csv_text = build_audit_log_csv(rows)
    records = read_csv(csv_text)

    assert csv_text.startswith(",".join(AUDIT_LOG_HEADERS))
    assert len(records) == 1
    assert records[0]["organization_id"] == str(organization.id)
    assert records[0]["actor_user_id"] == str(user.id)
    assert records[0]["action"] == AuditAction.DOCUMENT_UPLOADED.value
    assert records[0]["entity_type"] == AuditEntityType.DOCUMENT.value
    assert records[0]["summary"] == 'Uploaded, "document".'
    assert records[0]["metadata_json"].startswith('{"a_value"')
    assert '"safe_value":"kept"' in records[0]["metadata_json"]
    assert "secret" not in csv_text
    assert "argon2 hash" not in csv_text
    assert "Bearer" not in csv_text
    assert "eyJ" not in csv_text
    assert "/tmp/private" not in csv_text
    assert "Other organization" not in csv_text
    assert "Organization-null" not in csv_text


def test_audit_log_empty_export_returns_headers_only(session: Session) -> None:
    rows = list_audit_log_export_rows(session, organization_id=object_id())

    assert build_audit_log_csv(rows).splitlines() == [",".join(AUDIT_LOG_HEADERS)]


def test_export_builders_do_not_write_files_or_create_audit_entries(
    monkeypatch: pytest.MonkeyPatch,
    session: CommitTrackingSession,
    organization: Organization,
    user: User,
) -> None:
    document = create_document(
        session,
        organization=organization,
        user=user,
        filename="approved.pdf",
        status=DocumentStatus.APPROVED.value,
    )
    create_control_flag(
        session,
        document_id=document.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="High amount.",
    )
    before_count = count_audit_entries(session)

    def fail_open(*args: object, **kwargs: object) -> object:
        raise AssertionError("export builders must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "write_text", fail_open)
    monkeypatch.setattr(Path, "write_bytes", fail_open)

    approved_rows = list_approved_document_export_rows(
        session,
        organization_id=organization.id,
    )
    exception_rows = list_exception_report_export_rows(
        session,
        organization_id=organization.id,
    )
    audit_rows = list_audit_log_export_rows(session, organization_id=organization.id)

    build_approved_documents_csv(approved_rows)
    build_exceptions_report_csv(exception_rows)
    build_audit_log_csv(audit_rows)

    assert count_audit_entries(session) == before_count
    assert session.commit_count == 0


def test_export_rows_are_deterministic_for_documents_and_audit_entries(
    session: Session,
    organization: Organization,
    user: User,
) -> None:
    older = datetime(2026, 1, 1, tzinfo=UTC)
    newer = older + timedelta(days=1)
    old_doc = create_document(
        session,
        organization=organization,
        user=user,
        filename="old.pdf",
        status=DocumentStatus.APPROVED.value,
        hash_character="a",
        created_at=older,
    )
    new_doc = create_document(
        session,
        organization=organization,
        user=user,
        filename="new.pdf",
        status=DocumentStatus.APPROVED.value,
        hash_character="b",
        created_at=newer,
    )
    old_entry = create_audit_entry(
        session,
        organization_id=organization.id,
        actor_user_id=user.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=old_doc.id,
        summary="Old entry.",
    )
    new_entry = create_audit_entry(
        session,
        organization_id=organization.id,
        actor_user_id=user.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=new_doc.id,
        summary="New entry.",
    )
    old_entry.created_at = older
    new_entry.created_at = newer
    session.flush()

    approved_records = read_csv(
        build_approved_documents_csv(
            list_approved_document_export_rows(
                session,
                organization_id=organization.id,
            )
        )
    )
    audit_records = read_csv(
        build_audit_log_csv(
            list_audit_log_export_rows(session, organization_id=organization.id)
        )
    )

    assert [record["document_id"] for record in approved_records] == [
        str(new_doc.id),
        str(old_doc.id),
    ]
    assert [record["audit_entry_id"] for record in audit_records] == [
        str(new_entry.id),
        str(old_entry.id),
    ]


def object_id() -> UUID:
    return uuid4()
