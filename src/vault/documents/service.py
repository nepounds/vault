"""Service functions for Vault document metadata."""

from __future__ import annotations

import string
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from vault.documents.models import Document
from vault.documents.statuses import DocumentStatus
from vault.exceptions import DocumentNotFoundError, DocumentValidationError

_SHA256_HEX_LENGTH = 64
_LOWERCASE_HEX_DIGITS = frozenset(string.hexdigits.lower())


def create_document_metadata(
    session: Session,
    *,
    organization_id: UUID,
    uploaded_by_user_id: UUID,
    original_filename: str,
    stored_filename: str,
    content_type: str,
    file_size_bytes: int,
    sha256_hash: str,
) -> Document:
    """Create a document metadata record without handling file bytes."""
    clean_original_filename = _require_non_blank(
        original_filename,
        field_name="original_filename",
    )
    clean_stored_filename = _require_non_blank(
        stored_filename,
        field_name="stored_filename",
    )
    clean_content_type = _require_non_blank(
        content_type,
        field_name="content_type",
    )
    clean_sha256_hash = _validate_sha256_hash(sha256_hash)
    clean_file_size_bytes = _validate_file_size_bytes(file_size_bytes)

    document = Document(
        organization_id=organization_id,
        uploaded_by_user_id=uploaded_by_user_id,
        original_filename=clean_original_filename,
        stored_filename=clean_stored_filename,
        content_type=clean_content_type,
        file_size_bytes=clean_file_size_bytes,
        sha256_hash=clean_sha256_hash,
        status=DocumentStatus.PENDING.value,
    )
    session.add(document)
    session.flush()

    return document


def list_documents_for_organization(
    session: Session,
    *,
    organization_id: UUID,
) -> list[Document]:
    """List document metadata for one organization, newest first."""
    statement = (
        select(Document)
        .where(Document.organization_id == organization_id)
        .order_by(Document.created_at.desc(), Document.id.desc())
    )

    return list(session.scalars(statement))


def get_document_for_organization(
    session: Session,
    *,
    organization_id: UUID,
    document_id: UUID,
) -> Document | None:
    """Return one organization-scoped document, or None when missing."""
    statement = select(Document).where(
        Document.organization_id == organization_id,
        Document.id == document_id,
    )

    return session.scalar(statement)


def require_document_for_organization(
    session: Session,
    *,
    organization_id: UUID,
    document_id: UUID,
) -> Document:
    """Return one organization-scoped document or raise a safe not-found error."""
    document = get_document_for_organization(
        session,
        organization_id=organization_id,
        document_id=document_id,
    )
    if document is None:
        raise DocumentNotFoundError("Document was not found.")

    return document


def _require_non_blank(value: str, *, field_name: str) -> str:
    clean_value = value.strip()
    if not clean_value:
        raise DocumentValidationError(f"{field_name} is required")

    return clean_value


def _validate_file_size_bytes(file_size_bytes: int) -> int:
    if file_size_bytes <= 0:
        raise DocumentValidationError("file_size_bytes must be positive")

    return file_size_bytes


def _validate_sha256_hash(sha256_hash: str) -> str:
    clean_hash = _require_non_blank(sha256_hash, field_name="sha256_hash")

    if len(clean_hash) != _SHA256_HEX_LENGTH:
        raise DocumentValidationError("sha256_hash must be 64 lowercase hex characters")

    if any(character not in _LOWERCASE_HEX_DIGITS for character in clean_hash):
        raise DocumentValidationError("sha256_hash must be 64 lowercase hex characters")

    return clean_hash
