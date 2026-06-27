"""Thin command-line shell for Vault local workflows."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_PATH = _REPO_ROOT / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

if TYPE_CHECKING:
    from vault.exports.schemas import (
        ApprovedDocumentExportRow,
        AuditLogExportRow,
        ExceptionReportExportRow,
    )

APPROVED_DOCUMENTS_FILENAME = "approved_documents.csv"
EXCEPTIONS_REPORT_FILENAME = "exceptions_report.csv"
AUDIT_LOG_FILENAME = "audit_log.csv"
DEMO_EXPORT_FILENAMES = (
    APPROVED_DOCUMENTS_FILENAME,
    EXCEPTIONS_REPORT_FILENAME,
    AUDIT_LOG_FILENAME,
)

_DEMO_ORG_ID = UUID("11111111-1111-4111-8111-111111111111")
_DEMO_ACTOR_ID = UUID("22222222-2222-4222-8222-222222222222")
_DEMO_REVIEWER_ID = UUID("33333333-3333-4333-8333-333333333333")
_DOC_ACME_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
_DOC_BRIGHTLINE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
_DOC_COASTAL_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
_FLAG_BLOCKER_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
_FLAG_WARNING_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
_AUDIT_UPLOAD_ID = UUID("10101010-1010-4010-8010-101010101010")
_AUDIT_REVIEW_ID = UUID("20202020-2020-4020-8020-202020202020")
_AUDIT_STATUS_ID = UUID("30303030-3030-4030-8030-303030303030")
_AUDIT_EXPORT_ID = UUID("40404040-4040-4040-8040-404040404040")


def build_parser() -> argparse.ArgumentParser:
    """Build the Vault CLI parser."""
    parser = argparse.ArgumentParser(description="Vault local CLI helper.")
    subparsers = parser.add_subparsers(dest="command")

    export_demo_parser = subparsers.add_parser(
        "export-demo",
        help="Write deterministic fake demo CSV exports.",
    )
    export_demo_parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory where demo CSV files should be written.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Vault CLI shell."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "export-demo":
        return _run_export_demo(args.output_dir)

    parser.print_help()
    return 0


def export_demo(output_dir: Path) -> tuple[Path, Path, Path]:
    """Write deterministic fake demo export CSV files."""
    from vault.exports.builders import (
        build_approved_documents_csv,
        build_audit_log_csv,
        build_exceptions_report_csv,
    )

    if output_dir.exists() and not output_dir.is_dir():
        raise NotADirectoryError(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        APPROVED_DOCUMENTS_FILENAME: build_approved_documents_csv(
            _demo_approved_document_rows(),
        ),
        EXCEPTIONS_REPORT_FILENAME: build_exceptions_report_csv(
            _demo_exception_report_rows(),
        ),
        AUDIT_LOG_FILENAME: build_audit_log_csv(_demo_audit_log_rows()),
    }

    written_files: list[Path] = []
    for filename in DEMO_EXPORT_FILENAMES:
        target_path = output_dir / filename
        target_path.write_text(outputs[filename], encoding="utf-8")
        written_files.append(target_path)

    return (written_files[0], written_files[1], written_files[2])


def _run_export_demo(output_dir: Path) -> int:
    try:
        written_files = export_demo(output_dir)
    except OSError as exc:
        print(f"Failed to write demo exports: {exc}", file=sys.stderr)
        return 1

    print("Demo exports written:")
    for written_file in written_files:
        print(f"- {written_file}")

    return 0


def _demo_approved_document_rows() -> tuple[ApprovedDocumentExportRow, ...]:
    from vault.documents.statuses import DocumentStatus
    from vault.exports.schemas import ApprovedDocumentExportRow

    return (
        ApprovedDocumentExportRow(
            document_id=_DOC_ACME_ID,
            original_filename="acme-office-supplies.txt",
            status=DocumentStatus.APPROVED.value,
            vendor_name="Acme Demo Office Supplies",
            invoice_number="DEMO-1001",
            invoice_date=date(2026, 1, 5),
            due_date=date(2026, 2, 4),
            amount_cents=24875,
            currency="USD",
            category="Office Supplies",
            memo="Fake demo invoice for paper and toner.",
            created_at=_dt(2026, 1, 6, 14, 30),
        ),
        ApprovedDocumentExportRow(
            document_id=_DOC_BRIGHTLINE_ID,
            original_filename="brightline-consulting.txt",
            status=DocumentStatus.APPROVED.value,
            vendor_name=None,
            invoice_number=None,
            invoice_date=None,
            due_date=None,
            amount_cents=None,
            currency=None,
            category=None,
            memo=None,
            created_at=_dt(2026, 1, 7, 9, 15),
        ),
    )


def _demo_exception_report_rows() -> tuple[ExceptionReportExportRow, ...]:
    from vault.controls.severities import ControlFlagSeverity
    from vault.controls.types import ControlFlagType
    from vault.documents.statuses import DocumentStatus
    from vault.exports.schemas import ExceptionReportExportRow

    return (
        ExceptionReportExportRow(
            document_id=_DOC_COASTAL_ID,
            original_filename="coastal-utilities.txt",
            document_status=DocumentStatus.NEEDS_INFO.value,
            flag_id=_FLAG_BLOCKER_ID,
            flag_type=ControlFlagType.HIGH_AMOUNT.value,
            severity=ControlFlagSeverity.BLOCKER.value,
            reason="Fake invoice amount is above the demo review threshold.",
            created_at=_dt(2026, 1, 8, 11, 0),
        ),
        ExceptionReportExportRow(
            document_id=_DOC_BRIGHTLINE_ID,
            original_filename="brightline-consulting.txt",
            document_status=DocumentStatus.APPROVED.value,
            flag_id=_FLAG_WARNING_ID,
            flag_type=ControlFlagType.MISSING_INVOICE_DATE.value,
            severity=ControlFlagSeverity.WARNING.value,
            reason="Fake demo invoice is missing an invoice date.",
            created_at=_dt(2026, 1, 7, 10, 45),
        ),
    )


def _demo_audit_log_rows() -> tuple[AuditLogExportRow, ...]:
    from vault.audit.actions import AuditAction
    from vault.audit.entities import AuditEntityType
    from vault.documents.statuses import DocumentStatus
    from vault.exports.schemas import AuditLogExportRow

    return (
        AuditLogExportRow(
            audit_entry_id=_AUDIT_EXPORT_ID,
            organization_id=_DEMO_ORG_ID,
            actor_user_id=_DEMO_ACTOR_ID,
            action=AuditAction.EXPORT_GENERATED.value,
            entity_type=AuditEntityType.EXPORT.value,
            entity_id=None,
            summary="Generated fake demo audit-log export.",
            metadata_json={
                "export_type": "audit_log",
                "filename": AUDIT_LOG_FILENAME,
                "row_count": 3,
            },
            created_at=_dt(2026, 1, 8, 12, 5),
        ),
        AuditLogExportRow(
            audit_entry_id=_AUDIT_STATUS_ID,
            organization_id=_DEMO_ORG_ID,
            actor_user_id=_DEMO_REVIEWER_ID,
            action=AuditAction.DOCUMENT_STATUS_CHANGED.value,
            entity_type=AuditEntityType.DOCUMENT.value,
            entity_id=_DOC_ACME_ID,
            summary="Changed fake demo document status to approved.",
            metadata_json={
                "document_id": str(_DOC_ACME_ID),
                "new_status": DocumentStatus.APPROVED.value,
                "old_status": DocumentStatus.PENDING.value,
            },
            created_at=_dt(2026, 1, 6, 15, 10),
        ),
        AuditLogExportRow(
            audit_entry_id=_AUDIT_REVIEW_ID,
            organization_id=_DEMO_ORG_ID,
            actor_user_id=_DEMO_REVIEWER_ID,
            action=AuditAction.REVIEW_DECISION_CREATED.value,
            entity_type=AuditEntityType.REVIEW_DECISION.value,
            entity_id=UUID("50505050-5050-4050-8050-505050505050"),
            summary="Recorded fake demo approval decision.",
            metadata_json={
                "decision": "approved",
                "document_id": str(_DOC_ACME_ID),
                "resulting_status": DocumentStatus.APPROVED.value,
            },
            created_at=_dt(2026, 1, 6, 15, 9),
        ),
        AuditLogExportRow(
            audit_entry_id=_AUDIT_UPLOAD_ID,
            organization_id=_DEMO_ORG_ID,
            actor_user_id=_DEMO_ACTOR_ID,
            action=AuditAction.DOCUMENT_UPLOADED.value,
            entity_type=AuditEntityType.DOCUMENT.value,
            entity_id=_DOC_ACME_ID,
            summary="Uploaded fake demo document.",
            metadata_json={
                "content_type": "text/plain",
                "document_id": str(_DOC_ACME_ID),
                "file_size_bytes": 188,
                "original_filename": "acme-office-supplies.txt",
                "status": DocumentStatus.PENDING.value,
            },
            created_at=_dt(2026, 1, 6, 14, 30),
        ),
    )


def _dt(year: int, month: int, day: int, hour: int, minute: int) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


if __name__ == "__main__":
    raise SystemExit(main())
