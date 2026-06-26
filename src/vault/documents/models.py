"""SQLAlchemy models for Vault document metadata."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from vault.auth.models import utc_now
from vault.database import Base
from vault.documents.statuses import STATUS_VALUES, DocumentStatus

_STATUS_SQL_VALUES = ", ".join(f"'{status}'" for status in STATUS_VALUES)


class Document(Base):
    """Stored metadata for an uploaded accounting document."""

    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            f"status IN ({_STATUS_SQL_VALUES})",
            name="ck_documents_status_valid",
        ),
        Index("ix_documents_organization_id", "organization_id"),
        Index("ix_documents_organization_status", "organization_id", "status"),
        Index("ix_documents_sha256_hash", "sha256_hash"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=False,
    )
    uploaded_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=DocumentStatus.PENDING.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
