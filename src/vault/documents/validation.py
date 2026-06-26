"""Framework-independent upload metadata validation helpers."""

from __future__ import annotations

from dataclasses import dataclass

from vault.exceptions import DocumentUploadValidationError

MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = frozenset({".csv", ".txt", ".pdf"})
ALLOWED_CONTENT_TYPES = frozenset(
    {"text/csv", "text/plain", "application/pdf"},
)
_EXTENSION_CONTENT_TYPES = {
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
}


@dataclass(frozen=True, slots=True)
class ValidatedUploadMetadata:
    """Safe display metadata for an upload that passed MVP checks."""

    original_filename: str
    content_type: str
    file_size_bytes: int
    extension: str


def validate_upload_metadata(
    *,
    original_filename: str,
    content_type: str,
    file_size_bytes: int,
) -> ValidatedUploadMetadata:
    """Validate upload metadata before storage or document creation."""
    clean_filename = _validate_filename(original_filename)
    extension = _extract_extension(clean_filename)
    clean_content_type = _validate_content_type(content_type)
    clean_file_size = _validate_file_size(file_size_bytes)
    _validate_extension_content_type_match(
        extension=extension,
        content_type=clean_content_type,
    )

    return ValidatedUploadMetadata(
        original_filename=clean_filename,
        content_type=clean_content_type,
        file_size_bytes=clean_file_size,
        extension=extension,
    )


def _validate_filename(original_filename: str) -> str:
    clean_filename = original_filename.strip()

    if not clean_filename:
        raise DocumentUploadValidationError("original_filename is required")

    if "/" in clean_filename or "\\" in clean_filename:
        raise DocumentUploadValidationError("filename must not contain path separators")

    if ".." in clean_filename:
        raise DocumentUploadValidationError("filename must not contain path traversal")

    if clean_filename.startswith("."):
        raise DocumentUploadValidationError("filename must not be hidden")

    return clean_filename


def _extract_extension(filename: str) -> str:
    dot_index = filename.rfind(".")

    if dot_index <= 0 or dot_index == len(filename) - 1:
        raise DocumentUploadValidationError("filename must include an extension")

    extension = filename[dot_index:].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise DocumentUploadValidationError("file extension is not supported")

    return extension


def _validate_content_type(content_type: str) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise DocumentUploadValidationError("content type is not supported")

    return content_type


def _validate_file_size(file_size_bytes: int) -> int:
    if file_size_bytes <= 0:
        raise DocumentUploadValidationError("file size must be positive")

    if file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
        raise DocumentUploadValidationError("file size exceeds the maximum upload size")

    return file_size_bytes


def _validate_extension_content_type_match(
    *,
    extension: str,
    content_type: str,
) -> None:
    expected_content_type = _EXTENSION_CONTENT_TYPES[extension]
    if content_type != expected_content_type:
        raise DocumentUploadValidationError(
            "file extension and content type do not match",
        )
