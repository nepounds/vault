"""Official review decision values for Vault."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

ReviewDecisionValue = Literal["approved", "rejected", "needs_info"]


class ReviewDecisionValueEnum(StrEnum):
    """Allowed document review decision values."""

    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_INFO = "needs_info"


DECISION_VALUES: tuple[ReviewDecisionValue, ...] = (
    "approved",
    "rejected",
    "needs_info",
)
