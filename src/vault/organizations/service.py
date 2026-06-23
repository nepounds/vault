"""Organization creation services for Vault."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.exceptions import OrganizationValidationError
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole


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
