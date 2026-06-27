"""Create review decisions table.

Revision ID: 0007_create_review_decisions
Revises: 0006_create_control_flags
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_create_review_decisions"
down_revision: str | None = "0006_create_control_flags"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DECISION_VALUES = ("approved", "rejected", "needs_info")
_DECISION_SQL_VALUES = ", ".join(f"'{decision}'" for decision in _DECISION_VALUES)


def upgrade() -> None:
    """Create review decisions table."""
    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("reviewer_user_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("decision", sa.String(length=30), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"decision IN ({_DECISION_SQL_VALUES})",
            name="ck_review_decisions_decision_valid",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["reviewer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_review_decisions_document_id",
        "review_decisions",
        ["document_id"],
    )
    op.create_index(
        "ix_review_decisions_reviewer_user_id",
        "review_decisions",
        ["reviewer_user_id"],
    )
    op.create_index(
        "ix_review_decisions_decision",
        "review_decisions",
        ["decision"],
    )
    op.create_index(
        "ix_review_decisions_document_created_at",
        "review_decisions",
        ["document_id", "created_at"],
    )


def downgrade() -> None:
    """Drop review decisions table."""
    op.drop_index(
        "ix_review_decisions_document_created_at",
        table_name="review_decisions",
    )
    op.drop_index("ix_review_decisions_decision", table_name="review_decisions")
    op.drop_index(
        "ix_review_decisions_reviewer_user_id",
        table_name="review_decisions",
    )
    op.drop_index("ix_review_decisions_document_id", table_name="review_decisions")
    op.drop_table("review_decisions")
