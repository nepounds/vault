"""SQLAlchemy models for Vault organizations."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import UniqueConstraint

from vault.auth.models import utc_now
from vault.database import Base
from vault.organizations.roles import ROLE_VALUES

_ROLE_SQL_VALUES = ", ".join(f"'{role}'" for role in ROLE_VALUES)


class Organization(Base):
    """A tenant organization that owns accounting workflow data."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_by_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


class Membership(Base):
    """A user's role within an organization."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "user_id",
            name="uq_memberships_organization_user",
        ),
        CheckConstraint(
            f"role IN ({_ROLE_SQL_VALUES})",
            name="ck_memberships_role_valid",
        ),
        Index("ix_memberships_organization_id", "organization_id"),
        Index("ix_memberships_user_id", "user_id"),
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
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
