"""Create audit entries table.

Revision ID: 0008_create_audit_entries
Revises: 0007_create_review_decisions
Create Date: 2026-06-27
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_create_audit_entries"
down_revision: str | None = "0007_create_review_decisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUDIT_ACTION_VALUES = (
    "user_registered",
    "organization_created",
    "document_uploaded",
    "document_fact_created",
    "control_flags_generated",
    "duplicate_flags_generated",
    "review_decision_created",
    "document_status_changed",
    "export_generated",
)
_AUDIT_ENTITY_TYPE_VALUES = (
    "user",
    "organization",
    "document",
    "document_fact",
    "control_flag",
    "review_decision",
    "export",
)
_ACTION_SQL_VALUES = ", ".join(f"'{action}'" for action in _AUDIT_ACTION_VALUES)
_ENTITY_TYPE_SQL_VALUES = ", ".join(
    f"'{entity_type}'" for entity_type in _AUDIT_ENTITY_TYPE_VALUES
)


def upgrade() -> None:
    """Create audit entries table."""
    op.create_table(
        "audit_entries",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("actor_user_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("entity_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("summary", sa.String(length=500), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"action IN ({_ACTION_SQL_VALUES})",
            name="ck_audit_entries_action_valid",
        ),
        sa.CheckConstraint(
            f"entity_type IN ({_ENTITY_TYPE_SQL_VALUES})",
            name="ck_audit_entries_entity_type_valid",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"]),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_audit_entries_organization_id",
        "audit_entries",
        ["organization_id"],
    )
    op.create_index(
        "ix_audit_entries_actor_user_id",
        "audit_entries",
        ["actor_user_id"],
    )
    op.create_index("ix_audit_entries_action", "audit_entries", ["action"])
    op.create_index(
        "ix_audit_entries_entity_type",
        "audit_entries",
        ["entity_type"],
    )
    op.create_index(
        "ix_audit_entries_created_at",
        "audit_entries",
        ["created_at"],
    )
    op.create_index(
        "ix_audit_entries_organization_created_at",
        "audit_entries",
        ["organization_id", "created_at"],
    )
    op.create_index(
        "ix_audit_entries_entity_type_entity_id",
        "audit_entries",
        ["entity_type", "entity_id"],
    )


def downgrade() -> None:
    """Drop audit entries table."""
    op.drop_index(
        "ix_audit_entries_entity_type_entity_id",
        table_name="audit_entries",
    )
    op.drop_index(
        "ix_audit_entries_organization_created_at",
        table_name="audit_entries",
    )
    op.drop_index("ix_audit_entries_created_at", table_name="audit_entries")
    op.drop_index("ix_audit_entries_entity_type", table_name="audit_entries")
    op.drop_index("ix_audit_entries_action", table_name="audit_entries")
    op.drop_index("ix_audit_entries_actor_user_id", table_name="audit_entries")
    op.drop_index(
        "ix_audit_entries_organization_id",
        table_name="audit_entries",
    )
    op.drop_table("audit_entries")
