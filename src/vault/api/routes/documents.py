"""Document API routes for Vault."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from vault.api.dependencies import (
    get_current_user,
    get_database_session,
    require_organization_roles,
)
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.service import AuditMetadataValue, create_audit_entry
from vault.auth.models import User
from vault.config import load_settings
from vault.controls.models import ControlFlag
from vault.controls.schemas import ControlFlagResponse
from vault.controls.service import (
    generate_control_flags_for_document,
    generate_duplicate_control_flags_for_document,
    list_control_flags,
    require_control_flag,
)
from vault.documents.schemas import (
    DocumentFactCreateRequest,
    DocumentFactResponse,
    DocumentResponse,
    DocumentUploadResponse,
)
from vault.documents.service import (
    create_document_fact,
    create_document_metadata,
    list_document_facts,
    list_documents_for_organization,
    require_document_fact,
    require_document_for_organization,
)
from vault.documents.storage import store_upload_bytes
from vault.documents.validation import validate_upload_metadata
from vault.exceptions import (
    ControlFlagNotFoundError,
    DocumentFactNotFoundError,
    DocumentFactValidationError,
    DocumentNotFoundError,
    DocumentUploadValidationError,
    DocumentValidationError,
    ReviewDecisionNotFoundError,
    ReviewDecisionValidationError,
)
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.reviews.schemas import (
    ReviewDecisionCreateRequest,
    ReviewDecisionResponse,
)
from vault.reviews.service import (
    create_review_decision,
    list_review_decisions,
    require_review_decision,
)

router = APIRouter(prefix="/organizations", tags=["documents"])

ReadMembership = Annotated[
    Membership,
    Depends(
        require_organization_roles(
            MembershipRole.OWNER,
            MembershipRole.REVIEWER,
            MembershipRole.VIEWER,
        )
    ),
]


UploadMembership = Annotated[
    Membership,
    Depends(
        require_organization_roles(
            MembershipRole.OWNER,
            MembershipRole.REVIEWER,
        )
    ),
]


@router.get(
    "/{organization_id}/documents",
    response_model=list[DocumentResponse],
)
def list_documents(
    organization_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> list[DocumentResponse]:
    """List safe document metadata for an organization."""
    documents = list_documents_for_organization(
        session,
        organization_id=organization_id,
    )

    return [DocumentResponse.model_validate(document) for document in documents]


@router.get(
    "/{organization_id}/documents/{document_id}",
    response_model=DocumentResponse,
)
def read_document_detail(
    organization_id: UUID,
    document_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> DocumentResponse:
    """Return safe metadata for one organization-scoped document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    return DocumentResponse.model_validate(document)


@router.post(
    "/{organization_id}/documents/{document_id}/facts",
    response_model=DocumentFactResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_document_fact_route(
    organization_id: UUID,
    document_id: UUID,
    request: DocumentFactCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    _membership: UploadMembership,
) -> DocumentFactResponse:
    """Create one structured fact for an organization-scoped document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        fact = create_document_fact(
            session,
            document_id=document.id,
            vendor_name=request.vendor_name,
            invoice_number=request.invoice_number,
            invoice_date=request.invoice_date,
            due_date=request.due_date,
            amount_cents=request.amount_cents,
            currency=request.currency,
            category=request.category,
            memo=request.memo,
        )
        create_audit_entry(
            session,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.DOCUMENT_FACT_CREATED.value,
            entity_type=AuditEntityType.DOCUMENT_FACT.value,
            entity_id=fact.id,
            summary=f"Document fact created for document {document.id}",
            metadata_json={
                "document_id": str(document.id),
                "vendor_name": fact.vendor_name,
                "invoice_number": fact.invoice_number,
                "amount_cents": fact.amount_cents,
                "currency": fact.currency,
                "category": fact.category,
            },
        )
        session.commit()
        session.refresh(fact)
    except DocumentNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc
    except DocumentFactValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DocumentFactResponse.model_validate(fact)


@router.get(
    "/{organization_id}/documents/{document_id}/facts",
    response_model=list[DocumentFactResponse],
)
def list_document_facts_route(
    organization_id: UUID,
    document_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> list[DocumentFactResponse]:
    """List safe fact metadata for an organization-scoped document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    facts = list_document_facts(session, document_id=document.id)

    return [DocumentFactResponse.model_validate(fact) for fact in facts]


@router.get(
    "/{organization_id}/documents/{document_id}/facts/{fact_id}",
    response_model=DocumentFactResponse,
)
def read_document_fact_detail(
    organization_id: UUID,
    document_id: UUID,
    fact_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> DocumentFactResponse:
    """Return safe metadata for one organization-scoped document fact."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        fact = require_document_fact(
            session,
            document_id=document.id,
            fact_id=fact_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc
    except DocumentFactNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document fact was not found.",
        ) from exc

    return DocumentFactResponse.model_validate(fact)


@router.post(
    "/{organization_id}/documents/{document_id}/duplicates/generate",
    response_model=list[ControlFlagResponse],
)
def generate_duplicate_control_flags_route(
    organization_id: UUID,
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    _membership: UploadMembership,
) -> list[ControlFlagResponse]:
    """Generate safe duplicate-control flags for one document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        flags = generate_duplicate_control_flags_for_document(
            session,
            document_id=document.id,
        )
        create_audit_entry(
            session,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.DUPLICATE_FLAGS_GENERATED.value,
            entity_type=AuditEntityType.DOCUMENT.value,
            entity_id=document.id,
            summary=f"Duplicate flags generated for document {document.id}",
            metadata_json={
                "document_id": str(document.id),
                "generated_flag_count": len(flags),
                "generated_flags": _flag_metadata(flags),
            },
        )
        session.commit()
        for flag in flags:
            session.refresh(flag)
    except DocumentNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    return [ControlFlagResponse.model_validate(flag) for flag in flags]


@router.post(
    "/{organization_id}/documents/{document_id}/control-flags/generate",
    response_model=list[ControlFlagResponse],
)
def generate_control_flags_route(
    organization_id: UUID,
    document_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    _membership: UploadMembership,
) -> list[ControlFlagResponse]:
    """Generate safe control flags for an organization-scoped document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        flags = generate_control_flags_for_document(
            session,
            document_id=document.id,
        )
        create_audit_entry(
            session,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.CONTROL_FLAGS_GENERATED.value,
            entity_type=AuditEntityType.DOCUMENT.value,
            entity_id=document.id,
            summary=f"Control flags generated for document {document.id}",
            metadata_json={
                "document_id": str(document.id),
                "generated_flag_count": len(flags),
                "generated_flags": _flag_metadata(flags),
            },
        )
        session.commit()
        for flag in flags:
            session.refresh(flag)
    except DocumentNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    return [ControlFlagResponse.model_validate(flag) for flag in flags]


@router.get(
    "/{organization_id}/documents/{document_id}/control-flags",
    response_model=list[ControlFlagResponse],
)
def list_control_flags_route(
    organization_id: UUID,
    document_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> list[ControlFlagResponse]:
    """List safe control flag metadata for one document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    flags = list_control_flags(session, document_id=document.id)

    return [ControlFlagResponse.model_validate(flag) for flag in flags]


@router.get(
    "/{organization_id}/documents/{document_id}/control-flags/{flag_id}",
    response_model=ControlFlagResponse,
)
def read_control_flag_detail(
    organization_id: UUID,
    document_id: UUID,
    flag_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> ControlFlagResponse:
    """Return safe metadata for one document-scoped control flag."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        flag = require_control_flag(
            session,
            document_id=document.id,
            flag_id=flag_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc
    except ControlFlagNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control flag was not found.",
        ) from exc

    return ControlFlagResponse.model_validate(flag)


@router.post(
    "/{organization_id}/documents/{document_id}/review",
    response_model=ReviewDecisionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_review_decision_route(
    organization_id: UUID,
    document_id: UUID,
    request: ReviewDecisionCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    _membership: UploadMembership,
) -> ReviewDecisionResponse:
    """Create one review decision for an organization-scoped document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        old_status = document.status
        review_decision = create_review_decision(
            session,
            document_id=document.id,
            reviewer_user_id=current_user.id,
            decision=request.decision,
            reason=request.reason,
        )
        create_audit_entry(
            session,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.REVIEW_DECISION_CREATED.value,
            entity_type=AuditEntityType.REVIEW_DECISION.value,
            entity_id=review_decision.id,
            summary=f"Review decision created for document {document.id}",
            metadata_json={
                "document_id": str(document.id),
                "decision": review_decision.decision,
                "reason": review_decision.reason,
                "resulting_document_status": document.status,
            },
        )
        if old_status != document.status:
            create_audit_entry(
                session,
                organization_id=organization_id,
                actor_user_id=current_user.id,
                action=AuditAction.DOCUMENT_STATUS_CHANGED.value,
                entity_type=AuditEntityType.DOCUMENT.value,
                entity_id=document.id,
                summary=(
                    f"Document status changed from {old_status} "
                    f"to {document.status}"
                ),
                metadata_json={
                    "document_id": str(document.id),
                    "old_status": old_status,
                    "new_status": document.status,
                },
            )
        session.commit()
        session.refresh(review_decision)
        session.refresh(document)
    except DocumentNotFoundError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc
    except ReviewDecisionValidationError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return ReviewDecisionResponse.model_validate(review_decision)


@router.get(
    "/{organization_id}/documents/{document_id}/reviews",
    response_model=list[ReviewDecisionResponse],
)
def list_review_decisions_route(
    organization_id: UUID,
    document_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> list[ReviewDecisionResponse]:
    """List safe review decision metadata for one document."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc

    review_decisions = list_review_decisions(session, document_id=document.id)

    return [
        ReviewDecisionResponse.model_validate(review_decision)
        for review_decision in review_decisions
    ]


@router.get(
    "/{organization_id}/documents/{document_id}/reviews/{review_decision_id}",
    response_model=ReviewDecisionResponse,
)
def read_review_decision_detail(
    organization_id: UUID,
    document_id: UUID,
    review_decision_id: UUID,
    session: Annotated[Session, Depends(get_database_session)],
    _membership: ReadMembership,
) -> ReviewDecisionResponse:
    """Return safe metadata for one document-scoped review decision."""
    try:
        document = require_document_for_organization(
            session,
            organization_id=organization_id,
            document_id=document_id,
        )
        review_decision = require_review_decision(
            session,
            document_id=document.id,
            review_decision_id=review_decision_id,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document was not found.",
        ) from exc
    except ReviewDecisionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review decision was not found.",
        ) from exc

    return ReviewDecisionResponse.model_validate(review_decision)


@router.post(
    "/{organization_id}/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    organization_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_database_session)],
    _membership: UploadMembership,
    file: Annotated[UploadFile, File()],
) -> DocumentUploadResponse:
    """Upload a document file and create safe metadata for it."""
    known_upload_size = _known_upload_size(file)
    try:
        if known_upload_size is None:
            file_bytes = await file.read()
            upload_size = len(file_bytes)
        else:
            upload_size = known_upload_size

        metadata = validate_upload_metadata(
            original_filename=file.filename or "",
            content_type=file.content_type or "",
            file_size_bytes=upload_size,
        )
        if known_upload_size is not None:
            file_bytes = await file.read()
        stored_upload = store_upload_bytes(
            Path(load_settings().upload_dir),
            file_bytes,
            metadata.extension,
        )
        document = create_document_metadata(
            session,
            organization_id=organization_id,
            uploaded_by_user_id=current_user.id,
            original_filename=metadata.original_filename,
            stored_filename=stored_upload.stored_filename,
            content_type=metadata.content_type,
            file_size_bytes=stored_upload.file_size_bytes,
            sha256_hash=stored_upload.sha256_hash,
        )
        create_audit_entry(
            session,
            organization_id=organization_id,
            actor_user_id=current_user.id,
            action=AuditAction.DOCUMENT_UPLOADED.value,
            entity_type=AuditEntityType.DOCUMENT.value,
            entity_id=document.id,
            summary=f"Document uploaded: {document.original_filename}",
            metadata_json={
                "document_id": str(document.id),
                "original_filename": document.original_filename,
                "content_type": document.content_type,
                "file_size_bytes": document.file_size_bytes,
                "sha256_hash": document.sha256_hash,
                "status": document.status,
            },
        )
        session.commit()
        session.refresh(document)
    except (DocumentUploadValidationError, DocumentValidationError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DocumentUploadResponse.model_validate(document)


def _flag_metadata(flags: list[ControlFlag]) -> list[AuditMetadataValue]:
    return [
        {
            "flag_id": str(flag.id),
            "flag_type": flag.flag_type,
            "severity": flag.severity,
        }
        for flag in flags
    ]


def _known_upload_size(file: UploadFile) -> int | None:
    return file.size
