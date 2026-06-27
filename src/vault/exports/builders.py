"""Framework-independent CSV text builders for Vault exports."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable
from datetime import date, datetime
from uuid import UUID

from vault.audit.service import AuditMetadataValue
from vault.exports.schemas import (
    ApprovedDocumentExportRow,
    AuditLogExportRow,
    ExceptionReportExportRow,
)

APPROVED_DOCUMENTS_HEADERS = (
    "document_id",
    "original_filename",
    "status",
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "due_date",
    "amount_cents",
    "currency",
    "category",
    "memo",
    "created_at",
)

EXCEPTIONS_REPORT_HEADERS = (
    "document_id",
    "original_filename",
    "document_status",
    "flag_id",
    "flag_type",
    "severity",
    "reason",
    "created_at",
)

AUDIT_LOG_HEADERS = (
    "audit_entry_id",
    "organization_id",
    "actor_user_id",
    "action",
    "entity_type",
    "entity_id",
    "summary",
    "metadata_json",
    "created_at",
)


def build_approved_documents_csv(
    rows: Iterable[ApprovedDocumentExportRow],
) -> str:
    """Build approved-documents CSV text from typed export rows."""
    return _write_csv(
        APPROVED_DOCUMENTS_HEADERS,
        (
            (
                row.document_id,
                row.original_filename,
                row.status,
                row.vendor_name,
                row.invoice_number,
                row.invoice_date,
                row.due_date,
                row.amount_cents,
                row.currency,
                row.category,
                row.memo,
                row.created_at,
            )
            for row in rows
        ),
    )


def build_exceptions_report_csv(
    rows: Iterable[ExceptionReportExportRow],
) -> str:
    """Build exception-report CSV text from typed export rows."""
    return _write_csv(
        EXCEPTIONS_REPORT_HEADERS,
        (
            (
                row.document_id,
                row.original_filename,
                row.document_status,
                row.flag_id,
                row.flag_type,
                row.severity,
                row.reason,
                row.created_at,
            )
            for row in rows
        ),
    )


def build_audit_log_csv(rows: Iterable[AuditLogExportRow]) -> str:
    """Build audit-log CSV text from typed export rows."""
    return _write_csv(
        AUDIT_LOG_HEADERS,
        (
            (
                row.audit_entry_id,
                row.organization_id,
                row.actor_user_id,
                row.action,
                row.entity_type,
                row.entity_id,
                row.summary,
                _metadata_to_json(row.metadata_json),
                row.created_at,
            )
            for row in rows
        ),
    )


def _write_csv(headers: tuple[str, ...], rows: Iterable[tuple[object, ...]]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_format_csv_value(value) for value in row])

    return output.getvalue()


def _format_csv_value(value: object) -> str | int:
    if value is None:
        return ""

    if isinstance(value, datetime | date):
        return value.isoformat()

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, int):
        return value

    return str(value)


def _metadata_to_json(metadata: dict[str, AuditMetadataValue]) -> str:
    return json.dumps(metadata, sort_keys=True, separators=(",", ":"))
