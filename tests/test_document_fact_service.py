"""Tests for Vault document fact service behavior."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.documents.models import Document, DocumentFact
from vault.documents.service import (
    create_document_fact,
    create_document_metadata,
    get_document_fact,
    list_document_facts,
    require_document_fact,
)
from vault.exceptions import (
    DocumentFactNotFoundError,
    DocumentFactValidationError,
)
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


def create_valid_fact(
    session: Session,
    *,
    document: Document,
    vendor_name: str = "Example Vendor",
    invoice_number: str | None = "INV-100",
    invoice_date: date | None = date(2026, 1, 15),
    due_date: date | None = date(2026, 2, 15),
    amount_cents: int = 12345,
    currency: str = "USD",
    category: str = "Office Supplies",
    memo: str | None = "Monthly supplies",
) -> DocumentFact:
    return create_document_fact(
        session,
        document_id=document.id,
        vendor_name=vendor_name,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        due_date=due_date,
        amount_cents=amount_cents,
        currency=currency,
        category=category,
        memo=memo,
    )


def test_create_document_fact_stores_document_id(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document)

    assert fact.document_id == document.id


def test_create_document_fact_stores_vendor_name(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(
        session,
        document=document,
        vendor_name="Example Vendor LLC",
    )

    assert fact.vendor_name == "Example Vendor LLC"


def test_create_document_fact_stores_invoice_number(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(
        session,
        document=document,
        invoice_number="INV-200",
    )

    assert fact.invoice_number == "INV-200"


def test_create_document_fact_stores_invoice_date(
    session: Session,
    document: Document,
) -> None:
    invoice_date = date(2026, 3, 1)

    fact = create_valid_fact(
        session,
        document=document,
        invoice_date=invoice_date,
    )

    assert fact.invoice_date == invoice_date


def test_create_document_fact_stores_due_date(
    session: Session,
    document: Document,
) -> None:
    due_date = date(2026, 3, 31)

    fact = create_valid_fact(
        session,
        document=document,
        due_date=due_date,
    )

    assert fact.due_date == due_date


def test_create_document_fact_stores_amount_cents(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(
        session,
        document=document,
        amount_cents=98765,
    )

    assert fact.amount_cents == 98765


def test_create_document_fact_stores_currency(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, currency="EUR")

    assert fact.currency == "EUR"


def test_create_document_fact_stores_category(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, category="Software")

    assert fact.category == "Software"


def test_create_document_fact_stores_memo(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, memo="Annual renewal")

    assert fact.memo == "Annual renewal"


def test_create_document_fact_gets_id_after_flush(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document)

    assert fact.id is not None


def test_create_document_fact_does_not_commit_automatically(
    session: CommitTrackingSession,
    document: Document,
) -> None:
    create_valid_fact(session, document=document)

    assert session.commit_count == 0


def test_create_document_fact_trims_vendor_name(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, vendor_name="  Vendor  ")

    assert fact.vendor_name == "Vendor"


def test_create_document_fact_trims_invoice_number_if_provided(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, invoice_number="  INV-1  ")

    assert fact.invoice_number == "INV-1"


def test_create_document_fact_normalizes_currency_to_uppercase(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, currency=" usd ")

    assert fact.currency == "USD"


def test_create_document_fact_trims_category(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, category="  Meals  ")

    assert fact.category == "Meals"


def test_create_document_fact_trims_memo_if_provided(
    session: Session,
    document: Document,
) -> None:
    fact = create_valid_fact(session, document=document, memo="  Lunch receipt  ")

    assert fact.memo == "Lunch receipt"


@pytest.mark.parametrize("optional_value", ["", "   "])
def test_create_document_fact_converts_blank_optional_strings_to_none(
    session: Session,
    document: Document,
    optional_value: str,
) -> None:
    fact = create_valid_fact(
        session,
        document=document,
        invoice_number=optional_value,
        memo=optional_value,
    )

    assert fact.invoice_number is None
    assert fact.memo is None


@pytest.mark.parametrize("vendor_name", ["", "   "])
def test_create_document_fact_rejects_blank_vendor_name(
    session: Session,
    document: Document,
    vendor_name: str,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="vendor_name"):
        create_valid_fact(session, document=document, vendor_name=vendor_name)


@pytest.mark.parametrize("currency", ["", "   "])
def test_create_document_fact_rejects_blank_currency(
    session: Session,
    document: Document,
    currency: str,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="currency"):
        create_valid_fact(session, document=document, currency=currency)


@pytest.mark.parametrize(
    "currency",
    [
        "US",
        "USDD",
        "U1D",
        "12$",
    ],
)
def test_create_document_fact_rejects_malformed_currency(
    session: Session,
    document: Document,
    currency: str,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="currency"):
        create_valid_fact(session, document=document, currency=currency)


@pytest.mark.parametrize("category", ["", "   "])
def test_create_document_fact_rejects_blank_category(
    session: Session,
    document: Document,
    category: str,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="category"):
        create_valid_fact(session, document=document, category=category)


def test_create_document_fact_rejects_zero_amount(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="amount_cents"):
        create_valid_fact(session, document=document, amount_cents=0)


def test_create_document_fact_rejects_negative_amount(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(DocumentFactValidationError, match="amount_cents"):
        create_valid_fact(session, document=document, amount_cents=-1)


def test_create_document_fact_allows_optional_fields_to_be_omitted(
    session: Session,
    document: Document,
) -> None:
    fact = create_document_fact(
        session,
        document_id=document.id,
        vendor_name="Example Vendor",
        amount_cents=12345,
        currency="USD",
        category="Office Supplies",
    )

    assert fact.invoice_number is None
    assert fact.invoice_date is None
    assert fact.due_date is None
    assert fact.memo is None


def test_duplicate_document_facts_are_allowed_for_now(
    session: Session,
    document: Document,
) -> None:
    first_fact = create_valid_fact(session, document=document)
    second_fact = create_valid_fact(session, document=document)

    statement = select(DocumentFact).order_by(DocumentFact.created_at)
    facts = session.scalars(statement).all()

    assert facts == [first_fact, second_fact]
    assert first_fact.vendor_name == second_fact.vendor_name
    assert first_fact.invoice_number == second_fact.invoice_number
    assert first_fact.amount_cents == second_fact.amount_cents


def test_list_document_facts_returns_only_requested_document_facts(
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
    expected = create_valid_fact(session, document=document, vendor_name="Expected")
    create_valid_fact(session, document=other_document, vendor_name="Other")

    facts = list_document_facts(session, document_id=document.id)

    assert facts == [expected]


def test_list_document_facts_does_not_leak_facts_from_another_document(
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
    create_valid_fact(session, document=other_document, vendor_name="Other")

    facts = list_document_facts(session, document_id=document.id)

    assert facts == []


def test_list_document_facts_has_deterministic_ordering(
    session: Session,
    document: Document,
) -> None:
    later = create_valid_fact(session, document=document, vendor_name="Later")
    earlier = create_valid_fact(session, document=document, vendor_name="Earlier")
    same_time_second = create_valid_fact(
        session,
        document=document,
        vendor_name="Same Time Second",
    )
    same_time_first = create_valid_fact(
        session,
        document=document,
        vendor_name="Same Time First",
    )
    later.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    earlier.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    same_time_second.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    same_time_first.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    same_time_second.id = uuid.UUID("22222222-2222-4222-8222-222222222222")
    same_time_first.id = uuid.UUID("11111111-1111-4111-8111-111111111111")
    session.flush()

    facts = list_document_facts(session, document_id=document.id)

    assert facts == [earlier, later, same_time_first, same_time_second]


def test_get_document_fact_scopes_by_document_id_and_fact_id(
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
    fact = create_valid_fact(session, document=document)
    other_fact = create_valid_fact(session, document=other_document)

    found = get_document_fact(
        session,
        document_id=document.id,
        fact_id=fact.id,
    )
    cross_document = get_document_fact(
        session,
        document_id=document.id,
        fact_id=other_fact.id,
    )

    assert found == fact
    assert cross_document is None


def test_require_document_fact_raises_safe_exception_when_missing(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(DocumentFactNotFoundError, match="Document fact"):
        require_document_fact(
            session,
            document_id=document.id,
            fact_id=uuid.uuid4(),
        )


def test_get_document_fact_does_not_return_fact_from_another_document(
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
    other_fact = create_valid_fact(session, document=other_document)

    found = get_document_fact(
        session,
        document_id=document.id,
        fact_id=other_fact.id,
    )

    assert found is None
