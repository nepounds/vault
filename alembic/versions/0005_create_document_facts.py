"""Create document facts table.

Revision ID: 0005_create_document_facts
Revises: 0004_create_documents
Create Date: 2026-06-26
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_create_document_facts"
down_revision: str | None = "0004_create_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create document facts table."""
    op.create_table(
        "document_facts",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("document_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("vendor_name", sa.String(length=255), nullable=False),
        sa.Column("invoice_number", sa.String(length=80), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=False),
        sa.Column("memo", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "amount_cents > 0",
            name="ck_document_facts_amount_positive",
        ),
        sa.CheckConstraint(
            "length(currency) = 3 AND currency = upper(currency)",
            name="ck_document_facts_currency_uppercase_3",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_facts_document_id",
        "document_facts",
        ["document_id"],
    )
    op.create_index(
        "ix_document_facts_vendor_name",
        "document_facts",
        ["vendor_name"],
    )
    op.create_index(
        "ix_document_facts_invoice_number",
        "document_facts",
        ["invoice_number"],
    )
    op.create_index(
        "ix_document_facts_vendor_invoice_amount",
        "document_facts",
        ["vendor_name", "invoice_number", "amount_cents"],
    )


def downgrade() -> None:
    """Drop document facts table."""
    op.drop_index(
        "ix_document_facts_vendor_invoice_amount",
        table_name="document_facts",
    )
    op.drop_index("ix_document_facts_invoice_number", table_name="document_facts")
    op.drop_index("ix_document_facts_vendor_name", table_name="document_facts")
    op.drop_index("ix_document_facts_document_id", table_name="document_facts")
    op.drop_table("document_facts")
