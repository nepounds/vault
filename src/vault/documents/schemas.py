"""Pydantic schemas for Vault document APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from vault.documents.statuses import DocumentStatusValue


class DocumentUploadResponse(BaseModel):
    """Safe response body for uploaded document metadata."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    uploaded_by_user_id: UUID
    original_filename: str
    stored_filename: str
    content_type: str
    file_size_bytes: int
    sha256_hash: str
    status: DocumentStatusValue
    created_at: datetime
