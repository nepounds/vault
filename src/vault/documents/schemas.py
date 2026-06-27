"""Pydantic schemas for Vault document APIs."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from vault.documents.statuses import DocumentStatusValue


class DocumentResponse(BaseModel):
    """Safe response body for document metadata."""

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


class DocumentUploadResponse(DocumentResponse):
    """Safe response body for uploaded document metadata."""


class DocumentFactCreateRequest(BaseModel):
    """Request body for creating structured document facts."""

    vendor_name: str
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    amount_cents: int
    currency: str
    category: str
    memo: str | None = None


class DocumentFactResponse(BaseModel):
    """Safe response body for structured document facts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    vendor_name: str
    invoice_number: str | None
    invoice_date: date | None
    due_date: date | None
    amount_cents: int
    currency: str
    category: str
    memo: str | None
    created_at: datetime
