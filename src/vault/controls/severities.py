"""Official control flag severity values."""

from __future__ import annotations

from enum import StrEnum


class ControlFlagSeverity(StrEnum):
    """Supported control flag severities."""

    INFO = "info"
    WARNING = "warning"
    BLOCKER = "blocker"


SEVERITY_VALUES: tuple[str, ...] = tuple(
    severity.value for severity in ControlFlagSeverity
)
