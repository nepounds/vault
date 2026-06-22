"""Baseline migration.

Revision ID: 0001_baseline
Revises: None
Create Date: 2026-06-22
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Apply the empty baseline migration."""
    pass


def downgrade() -> None:
    """Reverse the empty baseline migration."""
    pass
