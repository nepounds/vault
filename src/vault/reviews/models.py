"""SQLAlchemy models for Vault review decisions."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from vault.auth.models import utc_now
from vault.database import Base
from vault.reviews.decisions import DECISION_VALUES

_DECISION_SQL_VALUES = ", ".join(f"'{decision}'" for decision in DECISION_VALUES)


class ReviewDecision(Base):
    """Reviewer decision linked to one uploaded document."""

    __tablename__ = "review_decisions"
    __table_args__ = (
        CheckConstraint(
            f"decision IN ({_DECISION_SQL_VALUES})",
            name="ck_review_decisions_decision_valid",
        ),
        Index("ix_review_decisions_document_id", "document_id"),
        Index("ix_review_decisions_reviewer_user_id", "reviewer_user_id"),
        Index("ix_review_decisions_decision", "decision"),
        Index(
            "ix_review_decisions_document_created_at",
            "document_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    document_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )
    reviewer_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
