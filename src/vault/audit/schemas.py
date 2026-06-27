"""Pydantic schemas for Vault audit APIs."""

from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from vault.audit.service import AuditMetadataValue

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
_WINDOWS_ABSOLUTE_PATH_PATTERN = re.compile(r"^[a-zA-Z]:[\\/]")


class AuditEntryResponse(BaseModel):
    """Safe response body for audit entry metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID | None
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    summary: str
    metadata_json: dict[str, AuditMetadataValue]
    created_at: datetime

    @field_validator("metadata_json", mode="before")
    @classmethod
    def sanitize_metadata(
        cls,
        value: object,
    ) -> dict[str, AuditMetadataValue]:
        """Return structured audit metadata with sensitive values redacted."""
        if not isinstance(value, dict):
            return {}

        return {
            str(key): _sanitize_metadata_value(str(key), item)
            for key, item in value.items()
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

    if isinstance(value, dict):
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
    if _WINDOWS_ABSOLUTE_PATH_PATTERN.match(value):
        return True
    return value.startswith("/")
