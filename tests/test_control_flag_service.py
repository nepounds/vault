"""Tests for Vault control flag service behavior."""

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
    create_control_flag,
    generate_control_flags_for_document,
    get_control_flag,
    list_control_flags,
    require_control_flag,
)
from vault.controls.severities import ControlFlagSeverity
from vault.controls.types import ControlFlagType
from vault.documents.models import Document, DocumentFact
from vault.documents.service import create_document_fact, create_document_metadata
from vault.exceptions import ControlFlagNotFoundError, ControlFlagValidationError
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64
SECOND_SHA256_HASH = "b" * 64


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
    result = create_organization(
        session,
        creator=uploader,
        name="Example Company",
    )

    return result.organization


@pytest.fixture
def document(
    session: Session,
    organization: Organization,
    uploader: User,
) -> Document:
    return create_document_metadata(
        session,
        organization_id=organization.id,
        uploaded_by_user_id=uploader.id,
        original_filename="invoice.pdf",
        stored_filename="safe-generated-name.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=VALID_SHA256_HASH,
    )


def create_second_document(
    session: Session,
    *,
    organization: Organization,
    uploader: User,
) -> Document:
    return create_document_metadata(
        session,
        organization_id=organization.id,
        uploaded_by_user_id=uploader.id,
        original_filename="second-invoice.pdf",
        stored_filename="second-safe-generated-name.pdf",
        content_type="application/pdf",
        file_size_bytes=2048,
        sha256_hash=SECOND_SHA256_HASH,
    )


def create_valid_flag(
    session: Session,
    *,
    document: Document,
    flag_type: str = ControlFlagType.MISSING_INVOICE_NUMBER.value,
    severity: str = ControlFlagSeverity.WARNING.value,
    reason: str = "Invoice number is missing.",
) -> ControlFlag:
    return create_control_flag(
        session,
        document_id=document.id,
        flag_type=flag_type,
        severity=severity,
        reason=reason,
    )


def create_fact(
    session: Session,
    *,
    document: Document,
    invoice_number: str | None = "INV-100",
    invoice_date: date | None = date(2026, 1, 15),
    due_date: date | None = date(2026, 2, 15),
    amount_cents: int = 99_999,
    currency: str = "USD",
) -> DocumentFact:
    return create_document_fact(
        session,
        document_id=document.id,
        vendor_name="Example Vendor",
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        amount_cents=amount_cents,
        currency=currency,
        category="Office Supplies",
        memo="Monthly supplies",
    )


def test_create_control_flag_stores_document_id(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(session, document=document)

    assert flag.document_id == document.id


def test_create_control_flag_stores_flag_type(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(
        session,
        document=document,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
    )

    assert flag.flag_type == ControlFlagType.HIGH_AMOUNT.value


def test_create_control_flag_stores_severity(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(
        session,
        document=document,
        severity=ControlFlagSeverity.BLOCKER.value,
    )

    assert flag.severity == ControlFlagSeverity.BLOCKER.value


def test_create_control_flag_stores_reason(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(session, document=document, reason="Needs review.")

    assert flag.reason == "Needs review."


def test_create_control_flag_gets_id_after_flush(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(session, document=document)

    assert flag.id is not None


def test_create_control_flag_does_not_commit_automatically(
    session: CommitTrackingSession,
    document: Document,
) -> None:
    create_valid_flag(session, document=document)

    assert session.commit_count == 0


def test_create_control_flag_trims_flag_type(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(
        session,
        document=document,
        flag_type=f" {ControlFlagType.MISSING_DUE_DATE.value} ",
    )

    assert flag.flag_type == ControlFlagType.MISSING_DUE_DATE.value


def test_create_control_flag_trims_severity(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(
        session,
        document=document,
        severity=f" {ControlFlagSeverity.INFO.value} ",
    )

    assert flag.severity == ControlFlagSeverity.INFO.value


def test_create_control_flag_trims_reason(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(session, document=document, reason="  Needs review.  ")

    assert flag.reason == "Needs review."


@pytest.mark.parametrize("flag_type", ["", "   "])
def test_blank_flag_type_is_rejected(
    session: Session,
    document: Document,
    flag_type: str,
) -> None:
    with pytest.raises(ControlFlagValidationError):
        create_valid_flag(session, document=document, flag_type=flag_type)


@pytest.mark.parametrize("severity", ["", "   "])
def test_blank_severity_is_rejected(
    session: Session,
    document: Document,
    severity: str,
) -> None:
    with pytest.raises(ControlFlagValidationError):
        create_valid_flag(session, document=document, severity=severity)


@pytest.mark.parametrize("reason", ["", "   "])
def test_blank_reason_is_rejected(
    session: Session,
    document: Document,
    reason: str,
) -> None:
    with pytest.raises(ControlFlagValidationError):
        create_valid_flag(session, document=document, reason=reason)


def test_unsupported_flag_type_is_rejected(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(ControlFlagValidationError):
        create_valid_flag(session, document=document, flag_type="not_supported")


def test_unsupported_severity_is_rejected(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(ControlFlagValidationError):
        create_valid_flag(session, document=document, severity="critical")


def test_duplicate_flags_are_allowed_for_now(
    session: Session,
    document: Document,
) -> None:
    first_flag = create_valid_flag(session, document=document)
    second_flag = create_valid_flag(session, document=document)

    assert first_flag.id != second_flag.id
    assert len(list_control_flags(session, document_id=document.id)) == 2


def test_list_control_flags_returns_only_requested_document_flags(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    expected_flag = create_valid_flag(session, document=document)
    create_valid_flag(session, document=other_document)

    assert list_control_flags(session, document_id=document.id) == [expected_flag]


def test_list_control_flags_does_not_leak_flags_from_another_document(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    leaked_flag = create_valid_flag(session, document=other_document)

    listed_flags = list_control_flags(session, document_id=document.id)

    assert leaked_flag not in listed_flags


def test_list_control_flags_has_deterministic_ordering(
    session: Session,
    document: Document,
) -> None:
    info_flag = create_valid_flag(
        session,
        document=document,
        flag_type=ControlFlagType.MISSING_DUE_DATE.value,
        severity=ControlFlagSeverity.INFO.value,
        reason="Due date is missing.",
    )
    blocker_flag = create_valid_flag(
        session,
        document=document,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="Amount is high.",
    )
    warning_flag = create_valid_flag(
        session,
        document=document,
        flag_type=ControlFlagType.MISSING_INVOICE_DATE.value,
        severity=ControlFlagSeverity.WARNING.value,
        reason="Invoice date is missing.",
    )

    listed_flags = list_control_flags(session, document_id=document.id)

    assert listed_flags == [blocker_flag, warning_flag, info_flag]


def test_get_control_flag_scopes_by_document_id_and_flag_id(
    session: Session,
    document: Document,
) -> None:
    flag = create_valid_flag(session, document=document)

    found_flag = get_control_flag(
        session,
        document_id=document.id,
        flag_id=flag.id,
    )

    assert found_flag == flag


def test_require_missing_control_flag_raises_safe_custom_exception(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(ControlFlagNotFoundError):
        require_control_flag(
            session,
            document_id=document.id,
            flag_id=uuid.uuid4(),
        )


def test_flag_from_another_document_is_not_returned_by_scoped_lookup(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    other_flag = create_valid_flag(session, document=other_document)

    found_flag = get_control_flag(
        session,
        document_id=document.id,
        flag_id=other_flag.id,
    )

    assert found_flag is None


def test_generation_creates_missing_invoice_number_flag(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {ControlFlagType.MISSING_INVOICE_NUMBER.value}


def test_generation_creates_missing_invoice_date_flag(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_date=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {ControlFlagType.MISSING_INVOICE_DATE.value}


def test_generation_creates_missing_due_date_flag(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, due_date=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {ControlFlagType.MISSING_DUE_DATE.value}


def test_generation_creates_non_usd_currency_flag(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, currency="EUR")

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {ControlFlagType.NON_USD_CURRENCY.value}


def test_generation_creates_high_amount_flag(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, amount_cents=100_000)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {ControlFlagType.HIGH_AMOUNT.value}


def test_generated_severities_match_official_values(
    session: Session,
    document: Document,
) -> None:
    create_fact(
        session,
        document=document,
        invoice_number=None,
        invoice_date=None,
        due_date=None,
        amount_cents=100_000,
        currency="EUR",
    )

    flags = generate_control_flags_for_document(session, document_id=document.id)
    severities = {flag.severity for flag in flags}

    assert severities == {
        ControlFlagSeverity.BLOCKER.value,
        ControlFlagSeverity.WARNING.value,
        ControlFlagSeverity.INFO.value,
    }


def test_generated_flag_types_match_official_values(
    session: Session,
    document: Document,
) -> None:
    create_fact(
        session,
        document=document,
        invoice_number=None,
        invoice_date=None,
        due_date=None,
        amount_cents=100_000,
        currency="EUR",
    )

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert _flag_types(flags) == {
        ControlFlagType.MISSING_INVOICE_NUMBER.value,
        ControlFlagType.MISSING_INVOICE_DATE.value,
        ControlFlagType.MISSING_DUE_DATE.value,
        ControlFlagType.NON_USD_CURRENCY.value,
        ControlFlagType.HIGH_AMOUNT.value,
    }


def test_generated_reasons_are_clear_non_blank_strings(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert all(flag.reason.strip() for flag in flags)
    assert all(len(flag.reason.split()) >= 5 for flag in flags)


def test_generation_returns_created_flags(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert flags == list_control_flags(session, document_id=document.id)


def test_generation_flushes_created_flags_so_ids_are_available(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert all(flag.id is not None for flag in flags)


def test_generation_does_not_commit_automatically(
    session: CommitTrackingSession,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    generate_control_flags_for_document(session, document_id=document.id)

    assert session.commit_count == 0


def test_generation_creates_no_flags_for_document_with_no_facts(
    session: Session,
    document: Document,
) -> None:
    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert flags == []


def test_generation_creates_no_flags_for_clean_fact(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert flags == []


def test_generation_only_inspects_facts_for_requested_document(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    create_fact(session, document=other_document, invoice_number=None)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert flags == []


def test_generation_does_not_create_duplicate_file_hash_flags_yet(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, amount_cents=100_000)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert ControlFlagType.DUPLICATE_FILE_HASH.value not in _flag_types(flags)


def test_generation_does_not_create_duplicate_invoice_attributes_flags_yet(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, amount_cents=100_000)

    flags = generate_control_flags_for_document(session, document_id=document.id)

    assert ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value not in _flag_types(
        flags
    )


def test_generated_flags_are_persisted(
    session: Session,
    document: Document,
) -> None:
    create_fact(session, document=document, invoice_number=None)

    generate_control_flags_for_document(session, document_id=document.id)
    stored_flags = list(session.scalars(select(ControlFlag)))

    assert len(stored_flags) == 1
    assert stored_flags[0].document_id == document.id


def _flag_types(flags: list[ControlFlag]) -> set[str]:
    return {flag.flag_type for flag in flags}
