"""Organization creation and membership access services for Vault."""

from __future__ import annotations

import uuid
from collections.abc import Iterable
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.exceptions import (
    OrganizationMembershipRequiredError,
    OrganizationRoleRequiredError,
    OrganizationValidationError,
)
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import ROLE_VALUES, MembershipRole, MembershipRoleValue

RoleInput = MembershipRole | str


@dataclass(frozen=True, slots=True)
class OrganizationCreation:
    """Organization and creator membership created together."""

    organization: Organization
    membership: Membership


def create_organization(
    session: Session,
    *,
    creator: User,
    name: str,
) -> OrganizationCreation:
    """Create an organization and owner membership for its creator."""
    clean_name = _normalize_organization_name(name)
    _ensure_creator_is_active(creator)

    organization = Organization()
    organization.id = uuid.uuid4()
    organization.name = clean_name
    organization.created_by_user_id = creator.id

    membership = Membership()
    membership.organization_id = organization.id
    membership.user_id = creator.id
    membership.role = MembershipRole.OWNER.value

    session.add_all([organization, membership])
    session.flush()

    return OrganizationCreation(
        organization=organization,
        membership=membership,
    )


def get_membership_for_user(
    session: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> Membership | None:
    """Return a user's membership in an organization, if one exists."""
    statement = select(Membership).where(
        Membership.organization_id == organization_id,
        Membership.user_id == user_id,
    )
    return session.scalar(statement)


def require_membership(
    session: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
) -> Membership:
    """Return a user's membership or raise a safe access error."""
    membership = get_membership_for_user(
        session,
        organization_id=organization_id,
        user_id=user_id,
    )
    if membership is None:
        raise OrganizationMembershipRequiredError(
            "organization access is not available."
        )
    return membership


def membership_has_role(
    membership: Membership,
    allowed_roles: Iterable[RoleInput],
) -> bool:
    """Return whether a membership has one of the explicitly allowed roles."""
    official_allowed_roles = _official_allowed_roles(allowed_roles)
    if membership.role not in ROLE_VALUES:
        return False
    return membership.role in official_allowed_roles


def require_membership_role(
    session: Session,
    *,
    organization_id: UUID,
    user_id: UUID,
    allowed_roles: Iterable[RoleInput],
) -> Membership:
    """Return a membership only when its role is explicitly allowed."""
    membership = require_membership(
        session,
        organization_id=organization_id,
        user_id=user_id,
    )
    if not membership_has_role(membership, allowed_roles):
        raise OrganizationRoleRequiredError("organization access is not available.")
    return membership


def _normalize_organization_name(name: str) -> str:
    clean_name = name.strip()
    if clean_name == "":
        raise OrganizationValidationError("organization name is required.")
    return clean_name


def _ensure_creator_is_active(creator: User) -> None:
    if not creator.is_active:
        raise OrganizationValidationError(
            "inactive users cannot create organizations."
        )


def _official_allowed_roles(
    allowed_roles: Iterable[RoleInput],
) -> set[MembershipRoleValue]:
    official_roles: set[MembershipRoleValue] = set()
    for role in allowed_roles:
        role_value = role.value if isinstance(role, MembershipRole) else role
        if role_value in ROLE_VALUES:
            official_roles.add(role_value)
    return official_roles
