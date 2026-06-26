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
from vault.documents.schemas import DocumentUploadResponse
from vault.documents.service import create_document_metadata
from vault.documents.storage import store_upload_bytes
from vault.documents.validation import validate_upload_metadata
from vault.exceptions import DocumentUploadValidationError, DocumentValidationError
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole

router = APIRouter(prefix="/organizations", tags=["documents"])

UploadMembership = Annotated[
    Membership,
    Depends(
        require_organization_roles(
            MembershipRole.OWNER,
            MembershipRole.REVIEWER,
        )
    ),
]


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
