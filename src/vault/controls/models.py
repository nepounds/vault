"""SQLAlchemy models for Vault control flags."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from vault.auth.models import utc_now
from vault.controls.severities import SEVERITY_VALUES
from vault.controls.types import FLAG_TYPE_VALUES
from vault.database import Base

_SEVERITY_SQL_VALUES = ", ".join(f"'{severity}'" for severity in SEVERITY_VALUES)
_FLAG_TYPE_SQL_VALUES = ", ".join(f"'{flag_type}'" for flag_type in FLAG_TYPE_VALUES)


class ControlFlag(Base):
    """Accounting-control issue linked to one uploaded document."""

    __tablename__ = "control_flags"
    __table_args__ = (
        CheckConstraint(
            f"severity IN ({_SEVERITY_SQL_VALUES})",
            name="ck_control_flags_severity_valid",
        ),
        CheckConstraint(
            f"flag_type IN ({_FLAG_TYPE_SQL_VALUES})",
            name="ck_control_flags_flag_type_valid",
        ),
        Index("ix_control_flags_document_id", "document_id"),
        Index("ix_control_flags_severity", "severity"),
        Index("ix_control_flags_flag_type", "flag_type"),
        Index("ix_control_flags_document_severity", "document_id", "severity"),
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
    flag_type: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
