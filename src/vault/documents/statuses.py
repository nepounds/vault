"""Official document status values for Vault."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

DocumentStatusValue = Literal["pending", "approved", "rejected", "needs_info"]


class DocumentStatus(StrEnum):
    """Allowed document review status values."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


STATUS_VALUES: tuple[DocumentStatusValue, ...] = (
    "pending",
    "approved",
    "rejected",
    "needs_info",
)
