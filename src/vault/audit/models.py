"""SQLAlchemy models for Vault audit entries."""

from __future__ import annotations

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from vault.audit.actions import AUDIT_ACTION_VALUES
from vault.audit.entities import AUDIT_ENTITY_TYPE_VALUES
from vault.auth.models import utc_now
from vault.database import Base

_ACTION_SQL_VALUES = ", ".join(f"'{action}'" for action in AUDIT_ACTION_VALUES)
_ENTITY_TYPE_SQL_VALUES = ", ".join(
    f"'{entity_type}'" for entity_type in AUDIT_ENTITY_TYPE_VALUES
)


class AuditEntry(Base):
    """Append-only audit metadata for important Vault activity."""

    __tablename__ = "audit_entries"
    __table_args__ = (
        CheckConstraint(
            f"action IN ({_ACTION_SQL_VALUES})",
            name="ck_audit_entries_action_valid",
        ),
        CheckConstraint(
            f"entity_type IN ({_ENTITY_TYPE_SQL_VALUES})",
            name="ck_audit_entries_entity_type_valid",
        ),
        Index("ix_audit_entries_organization_id", "organization_id"),
        Index("ix_audit_entries_actor_user_id", "actor_user_id"),
        Index("ix_audit_entries_action", "action"),
        Index("ix_audit_entries_entity_type", "entity_type"),
        Index("ix_audit_entries_created_at", "created_at"),
        Index(
            "ix_audit_entries_organization_created_at",
            "organization_id",
            "created_at",
        ),
        Index("ix_audit_entries_entity_type_entity_id", "entity_type", "entity_id"),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    organization_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id"),
        nullable=True,
    )
    actor_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
