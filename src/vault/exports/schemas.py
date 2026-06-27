"""Typed row data for Vault CSV exports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from vault.audit.service import AuditMetadataDict


@dataclass(frozen=True, slots=True)
class ApprovedDocumentExportRow:
    """One row in the approved-documents CSV export."""

    document_id: UUID
    original_filename: str
    status: str
    vendor_name: str | None
    invoice_number: str | None
    invoice_date: date | None
    due_date: date | None
    amount_cents: int | None
    currency: str | None
    category: str | None
    memo: str | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ExceptionReportExportRow:
    """One row in the exception-report CSV export."""

    document_id: UUID
    original_filename: str
    document_status: str
    flag_id: UUID
    flag_type: str
    severity: str
    reason: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AuditLogExportRow:
    """One row in the audit-log CSV export."""

    audit_entry_id: UUID
    organization_id: UUID
    actor_user_id: UUID | None
    action: str
    entity_type: str
    entity_id: UUID | None
    summary: str
    metadata_json: AuditMetadataDict
    created_at: datetime
