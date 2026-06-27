"""Tests for Vault review decision service behavior."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.documents.models import Document
from vault.documents.service import create_document_metadata
from vault.documents.statuses import DocumentStatus
from vault.exceptions import (
    ReviewDecisionNotFoundError,
    ReviewDecisionValidationError,
)
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization
from vault.reviews.decisions import ReviewDecisionValueEnum
from vault.reviews.models import ReviewDecision
from vault.reviews.service import (
    create_review_decision,
    get_review_decision,
    list_review_decisions,
    require_review_decision,
)

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
def reviewer(session: Session) -> User:
    return create_user(
        session,
        email="reviewer@example.com",
        raw_password="safe password",
        full_name="Reviewer Example",
    )


@pytest.fixture
def organization(session: Session, uploader: User) -> Organization:
    return create_organization(
        session,
        creator=uploader,
        name="Example Company",
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
        sha256_hash=VALID_SHA256_HASH,
    )


def create_document(
    session: Session,
    *,
    organization: Organization,
    uploader: User,
    original_filename: str,
    stored_filename: str,
    sha256_hash: str,
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


def create_second_document(
    session: Session,
    *,
    organization: Organization,
    uploader: User,
) -> Document:
    return create_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="second-invoice.pdf",
        stored_filename="second-safe-generated-name.pdf",
        sha256_hash=SECOND_SHA256_HASH,
    )


def create_valid_review_decision(
    session: Session,
    *,
    document: Document,
    reviewer: User,
    decision: str = ReviewDecisionValueEnum.APPROVED.value,
    reason: str = "Invoice was reviewed and approved.",
) -> ReviewDecision:
    return create_review_decision(
        session,
        document_id=document.id,
        reviewer_user_id=reviewer.id,
        decision=decision,
        reason=reason,
    )


def test_create_approved_review_decision_stores_document_id(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert review_decision.document_id == document.id


def test_create_approved_review_decision_stores_reviewer_user_id(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert review_decision.reviewer_user_id == reviewer.id


def test_create_approved_review_decision_stores_decision(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert review_decision.decision == ReviewDecisionValueEnum.APPROVED.value


def test_create_approved_review_decision_stores_reason(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        reason="Looks correct.",
    )

    assert review_decision.reason == "Looks correct."


def test_create_review_decision_gets_id_after_flush(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert review_decision.id is not None


def test_create_approved_review_decision_updates_document_status(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.APPROVED.value,
    )

    assert document.status == DocumentStatus.APPROVED.value


def test_create_rejected_review_decision_updates_document_status(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.REJECTED.value,
    )

    assert document.status == DocumentStatus.REJECTED.value


def test_create_needs_info_review_decision_updates_document_status(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.NEEDS_INFO.value,
    )

    assert document.status == DocumentStatus.NEEDS_INFO.value


def test_review_decision_service_does_not_commit_automatically(
    session: CommitTrackingSession,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert session.commit_count == 0


def test_decision_is_trimmed(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=f" {ReviewDecisionValueEnum.REJECTED.value} ",
    )

    assert review_decision.decision == ReviewDecisionValueEnum.REJECTED.value


def test_reason_is_trimmed(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        reason="  Needs a clearer invoice number.  ",
    )

    assert review_decision.reason == "Needs a clearer invoice number."


def test_blank_decision_is_rejected(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            decision="",
        )


def test_blank_reason_is_rejected(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            reason="",
        )


def test_whitespace_only_reason_is_rejected(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            reason="   ",
        )


def test_unsupported_decision_is_rejected(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            decision="escalated",
        )


def test_pending_decision_is_rejected(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            decision=DocumentStatus.PENDING.value,
        )


def test_missing_document_raises_safe_custom_exception(
    session: Session,
    reviewer: User,
) -> None:
    with pytest.raises(ReviewDecisionNotFoundError):
        create_review_decision(
            session,
            document_id=uuid.uuid4(),
            reviewer_user_id=reviewer.id,
            decision=ReviewDecisionValueEnum.APPROVED.value,
            reason="Looks correct.",
        )


@pytest.mark.parametrize(
    "decision",
    [
        ReviewDecisionValueEnum.APPROVED.value,
        ReviewDecisionValueEnum.REJECTED.value,
        ReviewDecisionValueEnum.NEEDS_INFO.value,
    ],
)
def test_reason_is_required_for_every_decision(
    session: Session,
    document: Document,
    reviewer: User,
    decision: str,
) -> None:
    with pytest.raises(ReviewDecisionValidationError):
        create_valid_review_decision(
            session,
            document=document,
            reviewer=reviewer,
            decision=decision,
            reason="",
        )


def test_multiple_review_decisions_for_same_document_are_allowed(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    first_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.NEEDS_INFO.value,
        reason="Needs the invoice date.",
    )
    second_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="The invoice date was added.",
    )

    assert first_decision.id != second_decision.id
    assert list_review_decisions(session, document_id=document.id) == [
        first_decision,
        second_decision,
    ]


def test_later_review_decisions_can_update_document_status_again(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="Looks correct.",
    )
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.REJECTED.value,
        reason="A later review found a mismatch.",
    )

    assert document.status == DocumentStatus.REJECTED.value


def test_listing_decisions_returns_only_decisions_for_requested_document(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
    reviewer: User,
) -> None:
    requested_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    create_valid_review_decision(
        session,
        document=other_document,
        reviewer=reviewer,
    )

    assert list_review_decisions(session, document_id=document.id) == [
        requested_decision,
    ]


def test_listing_decisions_does_not_leak_decisions_from_another_document(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
    reviewer: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    other_decision = create_valid_review_decision(
        session,
        document=other_document,
        reviewer=reviewer,
    )

    assert other_decision not in list_review_decisions(
        session,
        document_id=document.id,
    )


def test_listing_decisions_has_deterministic_ordering(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    first_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.NEEDS_INFO.value,
        reason="Needs more detail.",
    )
    second_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.REJECTED.value,
        reason="The detail still does not match.",
    )
    third_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="The detail was corrected.",
    )

    assert list_review_decisions(session, document_id=document.id) == [
        first_decision,
        second_decision,
        third_decision,
    ]


def test_getting_review_decision_scopes_by_document_id_and_decision_id(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    review_decision = create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    found_decision = get_review_decision(
        session,
        document_id=document.id,
        review_decision_id=review_decision.id,
    )

    assert found_decision is review_decision


def test_requiring_missing_review_decision_raises_safe_custom_exception(
    session: Session,
    document: Document,
) -> None:
    with pytest.raises(ReviewDecisionNotFoundError):
        require_review_decision(
            session,
            document_id=document.id,
            review_decision_id=uuid.uuid4(),
        )


def test_review_decision_from_another_document_is_not_returned(
    session: Session,
    document: Document,
    organization: Organization,
    uploader: User,
    reviewer: User,
) -> None:
    other_document = create_second_document(
        session,
        organization=organization,
        uploader=uploader,
    )
    other_decision = create_valid_review_decision(
        session,
        document=other_document,
        reviewer=reviewer,
    )

    found_decision = get_review_decision(
        session,
        document_id=document.id,
        review_decision_id=other_decision.id,
    )

    assert found_decision is None


def test_service_does_not_create_audit_entries_yet(
    session: Session,
    document: Document,
    reviewer: User,
) -> None:
    create_valid_review_decision(
        session,
        document=document,
        reviewer=reviewer,
    )

    assert "audit_entries" not in Base.metadata.tables
