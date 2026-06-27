"""Pydantic schemas for Vault control flag APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ControlFlagResponse(BaseModel):
    """Safe response body for accounting-control flag metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    flag_type: str
    severity: str
    reason: str
    created_at: datetime
