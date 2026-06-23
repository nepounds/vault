"""Pydantic schemas for Vault authentication APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class UserRegistrationRequest(BaseModel):
    """Request body for creating a Vault user account."""

    email: str
    password: str
    full_name: str

    @field_validator("email", "password", "full_name")
    @classmethod
    def require_not_blank(cls, value: str) -> str:
        """Reject string fields that are blank after trimming."""
        if value.strip() == "":
            raise ValueError("field is required")
        return value


class UserRegistrationResponse(BaseModel):
    """Safe response body for a newly registered Vault user."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    is_active: bool
    created_at: datetime


class UserLoginRequest(BaseModel):
    """Request body for authenticating a Vault user."""

    email: str
    password: str

    @field_validator("email", "password")
    @classmethod
    def require_not_blank(cls, value: str) -> str:
        """Reject string fields that are blank after trimming."""
        if value.strip() == "":
            raise ValueError("field is required")
        return value


class UserLoginResponse(BaseModel):
    """Response body returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"
