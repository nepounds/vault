"""Create control flags table.

Revision ID: 0006_create_control_flags
Revises: 0005_create_document_facts
Create Date: 2026-06-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_create_control_flags"
down_revision: str | None = "0005_create_document_facts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SEVERITY_VALUES = ("info", "warning", "blocker")
_FLAG_TYPE_VALUES = (
    "missing_invoice_number",
    "missing_invoice_date",
    "missing_due_date",
    "non_usd_currency",
    "high_amount",
    "duplicate_file_hash",
    "duplicate_invoice_attributes",
)
_SEVERITY_SQL_VALUES = ", ".join(f"'{severity}'" for severity in _SEVERITY_VALUES)
_FLAG_TYPE_SQL_VALUES = ", ".join(f"'{flag_type}'" for flag_type in _FLAG_TYPE_VALUES)


def upgrade() -> None:
    """Create control flags table."""
    op.create_table(
        "control_flags",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("flag_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"severity IN ({_SEVERITY_SQL_VALUES})",
            name="ck_control_flags_severity_valid",
        ),
        sa.CheckConstraint(
            f"flag_type IN ({_FLAG_TYPE_SQL_VALUES})",
            name="ck_control_flags_flag_type_valid",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_control_flags_document_id",
        "control_flags",
        ["document_id"],
    )
    op.create_index(
        "ix_control_flags_severity",
        "control_flags",
        ["severity"],
    )
    op.create_index(
        "ix_control_flags_flag_type",
        "control_flags",
        ["flag_type"],
    )
    op.create_index(
        "ix_control_flags_document_severity",
        "control_flags",
        ["document_id", "severity"],
    )


def downgrade() -> None:
    """Drop control flags table."""
    op.drop_index("ix_control_flags_document_severity", table_name="control_flags")
    op.drop_index("ix_control_flags_flag_type", table_name="control_flags")
    op.drop_index("ix_control_flags_severity", table_name="control_flags")
    op.drop_index("ix_control_flags_document_id", table_name="control_flags")
    op.drop_table("control_flags")
