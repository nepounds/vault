"""Official audit entity type values for Vault."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

AuditEntityTypeValue = Literal[
    "user",
    "organization",
    "document",
    "document_fact",
    "control_flag",
    "review_decision",
    "export",
]


class AuditEntityType(StrEnum):
    """Allowed audit entity type values."""

    USER = "user"
    ORGANIZATION = "organization"
    DOCUMENT = "document"
    DOCUMENT_FACT = "document_fact"
    CONTROL_FLAG = "control_flag"
    REVIEW_DECISION = "review_decision"
    EXPORT = "export"


AUDIT_ENTITY_TYPE_VALUES: tuple[AuditEntityTypeValue, ...] = (
    "user",
    "organization",
    "document",
    "document_fact",
    "control_flag",
    "review_decision",
    "export",
)
