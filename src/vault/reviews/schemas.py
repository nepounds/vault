"""Pydantic schemas for Vault review decision APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from vault.reviews.decisions import ReviewDecisionValue


class ReviewDecisionCreateRequest(BaseModel):
    """Request body for creating a review decision."""

    decision: str
    reason: str


class ReviewDecisionResponse(BaseModel):
    """Safe response body for review decision metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    reviewer_user_id: UUID
    decision: ReviewDecisionValue
    reason: str
    created_at: datetime
