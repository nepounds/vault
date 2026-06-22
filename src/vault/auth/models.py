"""SQLAlchemy models for Vault authentication."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from vault.database import Base


def utc_now() -> datetime:
    """Return the current UTC datetime for model defaults."""
    return datetime.now(UTC)


class User(Base):
    """A Vault user account.

    Passwords are never stored directly. The password_hash value is reserved
    for a future password hashing service.
    """

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
