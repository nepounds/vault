"""Service functions for Vault review decisions."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from vault.documents.models import Document
from vault.documents.statuses import DocumentStatus
from vault.exceptions import (
    ReviewDecisionNotFoundError,
    ReviewDecisionValidationError,
)
from vault.reviews.decisions import DECISION_VALUES, ReviewDecisionValueEnum
from vault.reviews.models import ReviewDecision

_DECISION_STATUS_MAP = {
    ReviewDecisionValueEnum.APPROVED.value: DocumentStatus.APPROVED.value,
    ReviewDecisionValueEnum.REJECTED.value: DocumentStatus.REJECTED.value,
    ReviewDecisionValueEnum.NEEDS_INFO.value: DocumentStatus.NEEDS_INFO.value,
}


def create_review_decision(
    session: Session,
    *,
    document_id: UUID,
    reviewer_user_id: UUID,
    decision: str,
    reason: str,
) -> ReviewDecision:
    """Create one review decision and update the linked document status."""
    document = session.get(Document, document_id)
    if document is None:
        raise ReviewDecisionNotFoundError("Document was not found.")

    clean_decision = _validate_decision(decision)
    clean_reason = _require_non_blank(reason, field_name="reason")

    review_decision = ReviewDecision(
        document_id=document.id,
        reviewer_user_id=reviewer_user_id,
        decision=clean_decision,
        reason=clean_reason,
    )
    document.status = _DECISION_STATUS_MAP[clean_decision]

    session.add(review_decision)
    session.flush()

    return review_decision


def list_review_decisions(
    session: Session,
    *,
    document_id: UUID,
) -> list[ReviewDecision]:
    """List review decisions for one document, oldest first."""
    statement = (
        select(ReviewDecision)
        .where(ReviewDecision.document_id == document_id)
        .order_by(ReviewDecision.created_at.asc(), ReviewDecision.id.asc())
    )

    return list(session.scalars(statement))


def get_review_decision(
    session: Session,
    *,
    document_id: UUID,
    review_decision_id: UUID,
) -> ReviewDecision | None:
    """Return one document-scoped review decision, or None when missing."""
    statement = select(ReviewDecision).where(
        ReviewDecision.document_id == document_id,
        ReviewDecision.id == review_decision_id,
    )

    return session.scalar(statement)


def require_review_decision(
    session: Session,
    *,
    document_id: UUID,
    review_decision_id: UUID,
) -> ReviewDecision:
    """Return one document-scoped review decision or raise not-found."""
    review_decision = get_review_decision(
        session,
        document_id=document_id,
        review_decision_id=review_decision_id,
    )
    if review_decision is None:
        raise ReviewDecisionNotFoundError("Review decision was not found.")

    return review_decision


def _validate_decision(decision: str) -> str:
    clean_decision = _require_non_blank(decision, field_name="decision")
    if clean_decision not in DECISION_VALUES:
        raise ReviewDecisionValidationError("decision is not supported")

    return clean_decision


def _require_non_blank(value: str, *, field_name: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise ReviewDecisionValidationError(f"{field_name} is required")

    return clean_value
