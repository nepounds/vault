"""Pydantic schemas for Vault organization APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from vault.organizations.roles import MembershipRoleValue


class OrganizationCreateRequest(BaseModel):
    """Request body for creating a Vault organization."""

    name: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        """Trim and reject blank organization names."""
        clean_name = value.strip()
        if clean_name == "":
            raise ValueError("organization name is required")
        return clean_name


class OrganizationCreateResponse(BaseModel):
    """Safe response body for a newly created organization."""

    id: UUID
    name: str
    created_by_user_id: UUID
    created_at: datetime
    membership_id: UUID
    role: MembershipRoleValue
