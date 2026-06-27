"""Organization routes for Vault."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vault.api.dependencies import (
    get_current_user,
    get_database_session,
    require_organization_roles,
)
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.service import create_audit_entry
from vault.auth.models import User
from vault.exceptions import OrganizationValidationError
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole
from vault.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationCreateResponse,
)
from vault.organizations.service import create_organization

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationDetailResponse(BaseModel):
    """Safe response body for an organization visible to a member."""

    id: UUID
    name: str
    created_by_user_id: UUID
    created_at: datetime


@router.post(
    "",
    response_model=OrganizationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_route(
    organization_request: OrganizationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
) -> OrganizationCreateResponse:
    """Create an organization for the authenticated active user."""
    try:
        result = create_organization(
            session,
            creator=current_user,
            name=organization_request.name,
        )
        create_audit_entry(
            session,
            organization_id=result.organization.id,
            actor_user_id=current_user.id,
            action=AuditAction.ORGANIZATION_CREATED.value,
            entity_type=AuditEntityType.ORGANIZATION.value,
            entity_id=result.organization.id,
            summary=f"Organization created: {result.organization.name}",
            metadata_json={
                "organization_id": str(result.organization.id),
                "name": result.organization.name,
                "created_by_user_id": str(current_user.id),
                "owner_membership_id": str(result.membership.id),
            },
        )
        session.commit()
        session.refresh(result.organization)
        session.refresh(result.membership)
    except OrganizationValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return OrganizationCreateResponse(
        id=result.organization.id,
        name=result.organization.name,
        created_by_user_id=result.organization.created_by_user_id,
        created_at=result.organization.created_at,
        membership_id=result.membership.id,
        role=cast("Literal['owner', 'reviewer', 'viewer']", result.membership.role),
    )

@router.get(
    "/{organization_id}",
    response_model=OrganizationDetailResponse,
)
def get_organization_route(
    organization_id: UUID,
    membership: Annotated[
        Membership,
        Depends(
            require_organization_roles(
                MembershipRole.OWNER,
                MembershipRole.REVIEWER,
                MembershipRole.VIEWER,
            )
        ),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> OrganizationDetailResponse:
    """Return safe organization data for an authenticated member."""
    organization = session.get(Organization, membership.organization_id)
    if organization is None or organization.id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization access is not available.",
        )

    return OrganizationDetailResponse(
        id=organization.id,
        name=organization.name,
        created_by_user_id=organization.created_by_user_id,
        created_at=organization.created_at,
    )
