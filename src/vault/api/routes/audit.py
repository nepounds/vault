"""Audit API routes for Vault."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from vault.api.dependencies import get_database_session, require_organization_roles
from vault.audit.schemas import AuditEntryResponse
from vault.audit.service import list_audit_entries, require_audit_entry
from vault.exceptions import AuditEntryNotFoundError, AuditEntryValidationError
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole

router = APIRouter(prefix="/organizations", tags=["audit"])

AuditReadMembership = Annotated[
    Membership,
    Depends(
        require_organization_roles(
            MembershipRole.OWNER,
            MembershipRole.REVIEWER,
            MembershipRole.VIEWER,
        )
    ),
]


@router.get(
    "/{organization_id}/audit",
    response_model=list[AuditEntryResponse],
)
def list_audit_entries_route(
    organization_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: AuditReadMembership,
    action: Annotated[str | None, Query()] = None,
    entity_type: Annotated[str | None, Query()] = None,
    entity_id: Annotated[UUID | None, Query()] = None,
) -> list[AuditEntryResponse]:
    """List safe audit entries for an organization."""
    try:
        audit_entries = list_audit_entries(
            session,
            organization_id=organization_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    except AuditEntryValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return [AuditEntryResponse.model_validate(entry) for entry in audit_entries]


@router.get(
    "/{organization_id}/audit/{audit_entry_id}",
    response_model=AuditEntryResponse,
)
def read_audit_entry_detail(
    organization_id: UUID,
    audit_entry_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: AuditReadMembership,
) -> AuditEntryResponse:
    """Return one safe organization-scoped audit entry."""
    try:
        audit_entry = require_audit_entry(
            session,
            organization_id=organization_id,
            audit_entry_id=audit_entry_id,
        )
    except AuditEntryNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit entry was not found.",
        ) from exc

    return AuditEntryResponse.model_validate(audit_entry)
