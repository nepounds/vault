"""CSV export API routes for Vault."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from vault.api.dependencies import (
    get_current_user,
    get_database_session,
    require_organization_roles,
)
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.service import create_audit_entry
from vault.auth.models import User
from vault.exports.builders import (
    build_approved_documents_csv,
    build_audit_log_csv,
    build_exceptions_report_csv,
)
from vault.exports.service import (
    list_approved_document_export_rows,
    list_audit_log_export_rows,
    list_exception_report_export_rows,
)
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole

router = APIRouter(prefix="/organizations", tags=["exports"])

ExportMembership = Annotated[
    Membership,
    Depends(
        require_organization_roles(
            MembershipRole.OWNER,
            MembershipRole.REVIEWER,
        )
    ),
]


def _csv_response(*, csv_text: str, filename: str) -> Response:
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _create_export_audit_entry(
    session: Session,
    *,
    organization_id: UUID,
    actor_user_id: UUID,
    export_type: str,
    filename: str,
    row_count: int,
) -> None:
    create_audit_entry(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=AuditAction.EXPORT_GENERATED.value,
        entity_type=AuditEntityType.EXPORT.value,
        entity_id=None,
        summary=f"Generated {export_type} CSV export.",
        metadata_json={
            "export_type": export_type,
            "filename": filename,
            "row_count": row_count,
        },
    )


@router.get("/{organization_id}/exports/approved-documents")
def export_approved_documents(
    organization_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    _membership: ExportMembership,
) -> Response:
    """Download approved documents for one organization as CSV."""
    filename = "approved_documents.csv"
    export_type = "approved_documents"
    rows = list_approved_document_export_rows(
        session,
        organization_id=organization_id,
    )
    csv_text = build_approved_documents_csv(rows)
    _create_export_audit_entry(
        session,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        export_type=export_type,
        filename=filename,
        row_count=len(rows),
    )
    session.commit()

    return _csv_response(csv_text=csv_text, filename=filename)


@router.get("/{organization_id}/exports/exceptions-report")
def export_exceptions_report(
    organization_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    _membership: ExportMembership,
) -> Response:
    """Download the exception report for one organization as CSV."""
    filename = "exceptions_report.csv"
    export_type = "exceptions_report"
    rows = list_exception_report_export_rows(
        session,
        organization_id=organization_id,
    )
    csv_text = build_exceptions_report_csv(rows)
    _create_export_audit_entry(
        session,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        export_type=export_type,
        filename=filename,
        row_count=len(rows),
    )
    session.commit()

    return _csv_response(csv_text=csv_text, filename=filename)


@router.get("/{organization_id}/exports/audit-log")
def export_audit_log(
    organization_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    _membership: ExportMembership,
) -> Response:
    """Download the audit log for one organization as CSV."""
    filename = "audit_log.csv"
    export_type = "audit_log"
    rows = list_audit_log_export_rows(session, organization_id=organization_id)
    csv_text = build_audit_log_csv(rows)
    _create_export_audit_entry(
        session,
        organization_id=organization_id,
        actor_user_id=current_user.id,
        export_type=export_type,
        filename=filename,
        row_count=len(rows),
    )
    session.commit()

    return _csv_response(csv_text=csv_text, filename=filename)
