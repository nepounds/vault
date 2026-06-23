"""Official organization membership roles for Vault."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

MembershipRoleValue = Literal["owner", "reviewer", "viewer"]


class MembershipRole(StrEnum):
    """Allowed role values for organization memberships."""

    OWNER = "owner"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


ROLE_VALUES: tuple[MembershipRoleValue, ...] = (
    "owner",
    "reviewer",
    "viewer",
)
