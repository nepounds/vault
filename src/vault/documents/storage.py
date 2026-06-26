"""Framework-independent upload byte storage helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from vault.documents.validation import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_BYTES
from vault.exceptions import DocumentUploadValidationError


@dataclass(frozen=True, slots=True)
class StoredUpload:
    """Metadata returned after upload bytes are stored on local disk."""

    stored_filename: str
    stored_path: Path
    file_size_bytes: int
    sha256_hash: str


def calculate_sha256(data: bytes) -> str:
    """Return the lowercase SHA-256 hexadecimal digest for bytes."""
    import hashlib

    return hashlib.sha256(data).hexdigest()


def generate_stored_filename(extension: str) -> str:
    """Generate a safe stored filename using only Vault-controlled text."""
    clean_extension = _validate_storage_extension(extension)
    return f"{uuid4().hex}{clean_extension}"


def store_upload_bytes(
    upload_dir: Path,
    data: bytes,
    extension: str,
) -> StoredUpload:
    """Store validated upload bytes under the supplied upload directory."""
    file_size_bytes = _validate_storage_size(data)
    stored_filename = generate_stored_filename(extension)

    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / stored_filename
    _ensure_path_stays_inside_upload_dir(
        upload_dir=upload_dir,
        stored_path=stored_path,
    )

    with stored_path.open("xb") as stored_file:
        stored_file.write(data)

    return StoredUpload(
        stored_filename=stored_filename,
        stored_path=stored_path,
        file_size_bytes=file_size_bytes,
        sha256_hash=calculate_sha256(data),
    )


def _validate_storage_extension(extension: str) -> str:
    if not extension or not extension.startswith("."):
        raise DocumentUploadValidationError("file extension is malformed")

    if "/" in extension or "\\" in extension:
        raise DocumentUploadValidationError("file extension is malformed")

    if extension.count(".") != 1 or extension == ".":
        raise DocumentUploadValidationError("file extension is malformed")

    if extension != extension.lower():
        raise DocumentUploadValidationError("file extension is malformed")

    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentUploadValidationError("file extension is not supported")

    return extension


def _validate_storage_size(data: bytes) -> int:
    file_size_bytes = len(data)

    if file_size_bytes <= 0:
        raise DocumentUploadValidationError("file bytes are required")

    if file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise DocumentUploadValidationError("file size exceeds the maximum upload size")

    return file_size_bytes


def _ensure_path_stays_inside_upload_dir(
    *,
    upload_dir: Path,
    stored_path: Path,
) -> None:
    expected_parent = upload_dir.resolve(strict=False)
    actual_parent = stored_path.parent.resolve(strict=False)

    if actual_parent != expected_parent:
        raise DocumentUploadValidationError("stored file path escaped upload directory")
