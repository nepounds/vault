"""Tests for Vault duplicate detection service behavior."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import date
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.controls.models import ControlFlag
from vault.controls.service import (
    find_duplicate_documents_by_hash,
    find_duplicate_invoice_facts,
    generate_duplicate_control_flags_for_document,
)
from vault.controls.severities import ControlFlagSeverity
from vault.controls.types import ControlFlagType
from vault.documents.models import Document, DocumentFact
from vault.documents.service import create_document_fact, create_document_metadata
from vault.documents.statuses import DocumentStatus
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization

DUPLICATE_SHA256_HASH = "a" * 64
UNIQUE_SHA256_HASH = "b" * 64
OTHER_SHA256_HASH = "c" * 64


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
def uploader(session: Session) -> User:
    return create_user(
        session,
        email="uploader@example.com",
        raw_password="safe password",
        full_name="Uploader Example",
    )


@pytest.fixture
def organization(session: Session, uploader: User) -> Organization:
    return create_organization(
        session,
        creator=uploader,
        name="Example Company",
    ).organization


@pytest.fixture
def other_organization(session: Session) -> Organization:
    other_user = create_user(
        session,
        email="other-uploader@example.com",
        raw_password="safe password",
        full_name="Other Uploader",
    )
    return create_organization(
        session,
        creator=other_user,
        name="Other Company",
    ).organization


@pytest.fixture
def document(
    session: Session,
    organization: Organization,
    uploader: User,
) -> Document:
    return create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="invoice.pdf",
        stored_filename="safe-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )


def create_document(
    session: Session,
    *,
    organization: Organization,
    uploader: User,
    original_filename: str,
    stored_filename: str,
    sha256_hash: str = UNIQUE_SHA256_HASH,
) -> Document:
    return create_document_metadata(
        session,
        organization_id=organization.id,
        uploaded_by_user_id=uploader.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=sha256_hash,
    )


def create_fact(
    session: Session,
    *,
    document: Document,
    vendor_name: str = "Example Vendor",
    invoice_number: str | None = "INV-100",
    amount_cents: int = 12_345,
) -> DocumentFact:
    return create_document_fact(
        session,
        document_id=document.id,
        vendor_name=vendor_name,
        invoice_number=invoice_number,
        invoice_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15),
        amount_cents=amount_cents,
        currency="USD",
        category="Office Supplies",
        memo="Monthly supplies",
    )


def test_duplicate_file_hash_helper_finds_same_organization_documents(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    duplicate_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    duplicates = find_duplicate_documents_by_hash(session, document_id=document.id)

    assert duplicates == [duplicate_document]


def test_duplicate_file_hash_helper_excludes_target_document(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    duplicates = find_duplicate_documents_by_hash(session, document_id=document.id)

    assert document not in duplicates


def test_duplicate_file_hash_helper_does_not_leak_other_organization_documents(
    session: Session,
    document: Document,
    other_organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=other_organization,
        uploader=uploader,
        original_filename="other-org.pdf",
        stored_filename="other-org-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    duplicates = find_duplicate_documents_by_hash(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_file_hash_helper_returns_empty_list_when_no_matches(
    session: Session,
    document: Document,
) -> None:
    duplicates = find_duplicate_documents_by_hash(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_file_hash_helper_returns_empty_list_for_missing_document(
    session: Session,
) -> None:
    duplicates = find_duplicate_documents_by_hash(
        session,
        document_id=uuid.uuid4(),
    )

    assert duplicates == []


def test_duplicate_invoice_helper_finds_same_org_matching_fact(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    duplicate_fact = create_fact(session, document=other_document)

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == [duplicate_fact]


def test_duplicate_invoice_helper_compares_against_other_documents_only(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document)

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_invoice_helper_excludes_facts_on_same_document(
    session: Session,
    document: Document,
) -> None:
    first_fact = create_fact(session, document=document)
    second_fact = create_fact(session, document=document)

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []
    assert first_fact not in duplicates
    assert second_fact not in duplicates


def test_duplicate_invoice_helper_does_not_leak_other_organization_facts(
    session: Session,
    document: Document,
    other_organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=other_organization,
        uploader=uploader,
        original_filename="other-org.pdf",
        stored_filename="other-org-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document)

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_invoice_helper_ignores_missing_invoice_numbers(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document, invoice_number=None)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document, invoice_number=None)

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_invoice_helper_ignores_blank_invoice_numbers(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    document_fact = DocumentFact(
        document_id=document.id,
        vendor_name="Example Vendor",
        invoice_number="   ",
        amount_cents=12_345,
        currency="USD",
        category="Office Supplies",
    )
    session.add(document_fact)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    other_fact = DocumentFact(
        document_id=other_document.id,
        vendor_name="Example Vendor",
        invoice_number="   ",
        amount_cents=12_345,
        currency="USD",
        category="Office Supplies",
    )
    session.add(other_fact)
    session.flush()

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_invoice_helper_uses_case_insensitive_vendor_matching(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document, vendor_name="Example Vendor")
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    duplicate_fact = create_fact(
        session,
        document=other_document,
        vendor_name="example vendor",
    )

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == [duplicate_fact]


def test_duplicate_invoice_helper_returns_empty_list_when_no_matches(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document, invoice_number="INV-200")

    duplicates = find_duplicate_invoice_facts(session, document_id=document.id)

    assert duplicates == []


def test_duplicate_generation_creates_duplicate_file_hash_flag(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert _flag_types(flags) == {ControlFlagType.DUPLICATE_FILE_HASH.value}


def test_duplicate_generation_creates_duplicate_invoice_attributes_flag(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document)

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert _flag_types(flags) == {
        ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value,
    }


def test_duplicate_generation_uses_expected_severities(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document)

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )
    severities_by_type = {flag.flag_type: flag.severity for flag in flags}

    assert severities_by_type[ControlFlagType.DUPLICATE_FILE_HASH.value] == (
        ControlFlagSeverity.BLOCKER.value
    )
    assert severities_by_type[
        ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value
    ] == ControlFlagSeverity.WARNING.value


def test_duplicate_generated_reasons_are_clear_non_blank_strings(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document)

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert all(flag.reason.strip() for flag in flags)
    assert any("file hash" in flag.reason for flag in flags)
    assert any("vendor/invoice/amount" in flag.reason for flag in flags)


def test_duplicate_generated_reasons_do_not_include_local_absolute_paths(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="C:\\tmp\\secret\\duplicate.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert flags
    assert all("C:\\" not in flag.reason for flag in flags)
    assert all("/tmp/" not in flag.reason for flag in flags)
    assert all("secret" not in flag.reason for flag in flags)


def test_duplicate_generation_returns_created_flags(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )
    stored_flags = list(session.scalars(select(ControlFlag)))

    assert flags == stored_flags


def test_duplicate_generation_flushes_created_flags_so_ids_are_available(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert all(flag.id is not None for flag in flags)


def test_duplicate_generation_does_not_commit_automatically(
    session: CommitTrackingSession,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    generate_duplicate_control_flags_for_document(session, document_id=document.id)

    assert session.commit_count == 0


def test_duplicate_generation_creates_no_flags_when_no_duplicates_exist(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document)

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert flags == []


def test_duplicate_generation_does_not_flag_cross_organization_duplicates(
    session: Session,
    document: Document,
    other_organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=other_organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )
    create_fact(session, document=document)
    other_document = create_document(
        session,
        organization=other_organization,
        uploader=uploader,
        original_filename="other.pdf",
        stored_filename="other-generated-name.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    create_fact(session, document=other_document)

    flags = generate_duplicate_control_flags_for_document(
        session,
        document_id=document.id,
    )

    assert flags == []


def test_duplicate_generation_does_not_update_document_status(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="duplicate.pdf",
        stored_filename="duplicate-generated-name.pdf",
        sha256_hash=DUPLICATE_SHA256_HASH,
    )

    generate_duplicate_control_flags_for_document(session, document_id=document.id)

    assert document.status == DocumentStatus.PENDING.value


def _flag_types(flags: list[ControlFlag]) -> set[str]:
    return {flag.flag_type for flag in flags}
