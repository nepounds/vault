"""Organization routes for Vault."""

from __future__ import annotations

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vault.api.dependencies import get_current_user, get_database_session
from vault.auth.models import User
from vault.exceptions import OrganizationValidationError
from vault.organizations.schemas import (
    OrganizationCreateRequest,
    OrganizationCreateResponse,
)
from vault.organizations.service import create_organization

router = APIRouter(prefix="/organizations", tags=["organizations"])


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