"""Database-backed row queries for Vault CSV exports."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.orm import Session

from vault.audit.models import AuditEntry
from vault.audit.service import sanitize_audit_metadata
from vault.controls.models import ControlFlag
from vault.controls.severities import ControlFlagSeverity
from vault.documents.models import Document, DocumentFact
from vault.documents.statuses import DocumentStatus
from vault.exports.schemas import (
    ApprovedDocumentExportRow,
    AuditLogExportRow,
    ExceptionReportExportRow,
)

_SEVERITY_ORDER = case(
    (ControlFlag.severity == ControlFlagSeverity.BLOCKER.value, 0),
    (ControlFlag.severity == ControlFlagSeverity.WARNING.value, 1),
    (ControlFlag.severity == ControlFlagSeverity.INFO.value, 2),
    else_=3,
)


def list_approved_document_export_rows(
    session: Session,
    *,
    organization_id: UUID,
) -> list[ApprovedDocumentExportRow]:
    """Return approved-document export rows for one organization."""
    statement = (
        select(Document, DocumentFact)
        .outerjoin(DocumentFact, DocumentFact.document_id == Document.id)
        .where(
            Document.organization_id == organization_id,
            Document.status == DocumentStatus.APPROVED.value,
        )
        .order_by(
            Document.created_at.desc(),
            Document.id.desc(),
            DocumentFact.created_at.asc(),
            DocumentFact.id.asc(),
        )
    )

    rows: list[ApprovedDocumentExportRow] = []
    for document, fact in session.execute(statement):
        rows.append(_approved_document_row(document=document, fact=fact))

    return rows


def list_exception_report_export_rows(
    session: Session,
    *,
    organization_id: UUID,
) -> list[ExceptionReportExportRow]:
    """Return exception-report rows for one organization."""
    statement = (
        select(Document, ControlFlag)
        .join(ControlFlag, ControlFlag.document_id == Document.id)
        .where(Document.organization_id == organization_id)
        .order_by(
            _SEVERITY_ORDER,
            ControlFlag.created_at.desc(),
            ControlFlag.id.desc(),
        )
    )

    return [
        ExceptionReportExportRow(
            document_id=document.id,
            original_filename=document.original_filename,
            document_status=document.status,
            flag_id=flag.id,
            flag_type=flag.flag_type,
            severity=flag.severity,
            reason=flag.reason,
            created_at=flag.created_at,
        )
        for document, flag in session.execute(statement)
    ]


def list_audit_log_export_rows(
    session: Session,
    *,
    organization_id: UUID,
) -> list[AuditLogExportRow]:
    """Return safe audit-log export rows for one organization."""
    statement = (
        select(AuditEntry)
        .where(AuditEntry.organization_id == organization_id)
        .order_by(AuditEntry.created_at.desc(), AuditEntry.id.desc())
    )

    return [
        AuditLogExportRow(
            audit_entry_id=entry.id,
            organization_id=entry.organization_id,
            actor_user_id=entry.actor_user_id,
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            summary=entry.summary,
            metadata_json=sanitize_audit_metadata(entry.metadata_json),
            created_at=entry.created_at,
        )
        for entry in session.scalars(statement)
        if entry.organization_id is not None
    ]


def _approved_document_row(
    *,
    document: Document,
    fact: DocumentFact | None,
) -> ApprovedDocumentExportRow:
    return ApprovedDocumentExportRow(
        document_id=document.id,
        original_filename=document.original_filename,
        status=document.status,
        vendor_name=None if fact is None else fact.vendor_name,
        invoice_number=None if fact is None else fact.invoice_number,
        invoice_date=None if fact is None else fact.invoice_date,
        due_date=None if fact is None else fact.due_date,
        amount_cents=None if fact is None else fact.amount_cents,
        currency=None if fact is None else fact.currency,
        category=None if fact is None else fact.category,
        memo=None if fact is None else fact.memo,
        created_at=document.created_at,
    )
