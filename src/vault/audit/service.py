"""Service functions for Vault audit entries."""

from __future__ import annotations

from collections.abc import Mapping
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from vault.audit.actions import AUDIT_ACTION_VALUES
from vault.audit.entities import AUDIT_ENTITY_TYPE_VALUES
from vault.audit.models import AuditEntry
from vault.exceptions import AuditEntryNotFoundError, AuditEntryValidationError

type AuditMetadataValue = (
    str
    | int
    | float
    | bool
    | None
    | list[AuditMetadataValue]
    | dict[str, AuditMetadataValue]
)
type AuditMetadata = Mapping[str, AuditMetadataValue]
type AuditMetadataDict = dict[str, AuditMetadataValue]



_REDACTED = "[redacted]"
_SENSITIVE_KEY_PARTS = (
    "password",
    "password_hash",
    "hash",
    "authorization",
    "bearer",
    "token",
    "token_payload",
    "access_token",
    "refresh_token",
    "stored_path",
    "absolute_path",
    "local_path",
    "file_path",
)


def sanitize_audit_metadata(metadata: object) -> AuditMetadataDict:
    """Return audit metadata with risky values redacted for external output."""
    if not isinstance(metadata, Mapping):
        return {}

    return {
        str(key): _sanitize_metadata_value(str(key), value)
        for key, value in metadata.items()
    }


def _sanitize_metadata_value(
    key: str,
    value: object,
) -> AuditMetadataValue:
    if _is_sensitive_key(key):
        return _REDACTED

    if isinstance(value, str):
        if _is_sensitive_string(value):
            return _REDACTED
        return value

    if isinstance(value, bool) or value is None:
        return value

    if isinstance(value, int | float):
        return value

    if isinstance(value, list):
        return [_sanitize_metadata_value(key, item) for item in value]

    if isinstance(value, Mapping):
        return {
            str(item_key): _sanitize_metadata_value(str(item_key), item_value)
            for item_key, item_value in value.items()
        }

    return str(value)


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _is_sensitive_string(value: str) -> bool:
    normalized = value.lower().strip()
    if normalized.startswith("bearer "):
        return True
    if "eyj" in normalized and "." in normalized:
        return True
    if len(value) >= 3 and value[1:3] in {":\\", ":/"}:
        return value[0].isalpha()
    return value.startswith("/")


class _MetadataOmitted:
    """Sentinel for omitted audit metadata."""


_METADATA_OMITTED = _MetadataOmitted()


def create_audit_entry(
    session: Session,
    *,
    organization_id: UUID | None = None,
    actor_user_id: UUID | None = None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    summary: str,
    metadata_json: AuditMetadata | None | _MetadataOmitted = _METADATA_OMITTED,
) -> AuditEntry:
    """Create one audit entry without committing the session."""
    clean_action = _validate_action(action)
    clean_entity_type = _validate_entity_type(entity_type)
    clean_summary = _require_non_blank(summary, field_name="summary")
    clean_metadata = _copy_metadata(metadata_json)

    audit_entry = AuditEntry(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=clean_action,
        entity_type=clean_entity_type,
        entity_id=entity_id,
        summary=clean_summary,
        metadata_json=clean_metadata,
    )

    session.add(audit_entry)
    session.flush()

    return audit_entry


def list_audit_entries(
    session: Session,
    *,
    organization_id: UUID,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: UUID | None = None,
) -> list[AuditEntry]:
    """List audit entries for one organization, newest first."""
    filters = [AuditEntry.organization_id == organization_id]
    if action is not None:
        filters.append(AuditEntry.action == _validate_action(action))
    if entity_type is not None:
        filters.append(AuditEntry.entity_type == _validate_entity_type(entity_type))
    if entity_id is not None:
        filters.append(AuditEntry.entity_id == entity_id)

    statement = (
        select(AuditEntry)
        .where(*filters)
        .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
    )

    return list(session.scalars(statement))


def list_audit_entries_for_entity(
    session: Session,
    *,
    entity_type: str,
    entity_id: UUID,
) -> list[AuditEntry]:
    """List audit entries for one entity, newest first."""
    clean_entity_type = _validate_entity_type(entity_type)
    statement = (
        select(AuditEntry)
        .where(
            AuditEntry.entity_type == clean_entity_type,
            AuditEntry.entity_id == entity_id,
        )
        .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
    )

    return list(session.scalars(statement))


def get_audit_entry(
    session: Session,
    *,
    organization_id: UUID,
    audit_entry_id: UUID,
) -> AuditEntry | None:
    """Return one organization-scoped audit entry, or None when missing."""
    statement = select(AuditEntry).where(
        AuditEntry.organization_id == organization_id,
        AuditEntry.id == audit_entry_id,
    )

    return session.scalar(statement)


def require_audit_entry(
    session: Session,
    *,
    organization_id: UUID,
    audit_entry_id: UUID,
) -> AuditEntry:
    """Return one organization-scoped audit entry or raise not-found."""
    audit_entry = get_audit_entry(
        session,
        organization_id=organization_id,
        audit_entry_id=audit_entry_id,
    )
    if audit_entry is None:
        raise AuditEntryNotFoundError("Audit entry was not found.")

    return audit_entry


def _validate_action(action: str) -> str:
    clean_action = _require_non_blank(action, field_name="action")
    if clean_action not in AUDIT_ACTION_VALUES:
        raise AuditEntryValidationError("action is not supported")

    return clean_action


def _validate_entity_type(entity_type: str) -> str:
    clean_entity_type = _require_non_blank(entity_type, field_name="entity_type")
    if clean_entity_type not in AUDIT_ENTITY_TYPE_VALUES:
        raise AuditEntryValidationError("entity_type is not supported")

    return clean_entity_type


def _require_non_blank(value: str, *, field_name: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise AuditEntryValidationError(f"{field_name} is required")

    return clean_value


def _copy_metadata(
    metadata_json: AuditMetadata | None | _MetadataOmitted,
) -> AuditMetadataDict:
    if isinstance(metadata_json, _MetadataOmitted):
        return {}

    if metadata_json is None or not isinstance(metadata_json, Mapping):
        raise AuditEntryValidationError("metadata_json must be an object")

    return {
        key: _copy_metadata_value(value)
        for key, value in metadata_json.items()
    }


def _copy_metadata_value(value: AuditMetadataValue) -> AuditMetadataValue:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):
        return [_copy_metadata_value(item) for item in value]

    if isinstance(value, dict):
        return {key: _copy_metadata_value(item) for key, item in value.items()}

    return value
