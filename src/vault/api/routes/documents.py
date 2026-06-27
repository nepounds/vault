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
from vault.auth.models import User
from vault.config import load_settings
from vault.controls.schemas import ControlFlagResponse
from vault.controls.service import (
    generate_control_flags_for_document,
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
)
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole

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
    "/{organization_id}/documents/{document_id}/control-flags/generate",
    response_model=list[ControlFlagResponse],
)
def generate_control_flags_route(
    organization_id: UUID,
    document_id: UUID,
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
        session.commit()
        session.refresh(document)
    except (DocumentUploadValidationError, DocumentValidationError) as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DocumentUploadResponse.model_validate(document)


def _known_upload_size(file: UploadFile) -> int | None:
    return file.size
