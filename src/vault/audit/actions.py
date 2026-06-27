"""Official audit action values for Vault."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

AuditActionValue = Literal[
    "user_registered",
    "organization_created",
    "document_uploaded",
    "document_fact_created",
    "control_flags_generated",
    "duplicate_flags_generated",
    "review_decision_created",
    "document_status_changed",
    "export_generated",
]


class AuditAction(StrEnum):
    """Allowed audit action values."""

    USER_REGISTERED = "user_registered"
    ORGANIZATION_CREATED = "organization_created"
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_FACT_CREATED = "document_fact_created"
    CONTROL_FLAGS_GENERATED = "control_flags_generated"
    DUPLICATE_FLAGS_GENERATED = "duplicate_flags_generated"
    REVIEW_DECISION_CREATED = "review_decision_created"
    DOCUMENT_STATUS_CHANGED = "document_status_changed"
    EXPORT_GENERATED = "export_generated"


AUDIT_ACTION_VALUES: tuple[AuditActionValue, ...] = (
    "user_registered",
    "organization_created",
    "document_uploaded",
    "document_fact_created",
    "control_flags_generated",
    "duplicate_flags_generated",
    "review_decision_created",
    "document_status_changed",
    "export_generated",
)
