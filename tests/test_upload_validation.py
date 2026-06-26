"""Tests for upload metadata validation helpers."""

from __future__ import annotations

import builtins
from pathlib import Path
from typing import NoReturn

import pytest

from vault.documents.validation import (
    MAX_UPLOAD_SIZE_BYTES,
    validate_upload_metadata,
)
from vault.exceptions import DocumentUploadValidationError


def test_valid_csv_metadata_is_accepted() -> None:
    result = validate_upload_metadata(
        original_filename="invoice.csv",
        content_type="text/csv",
        file_size_bytes=1024,
    )

    assert result.original_filename == "invoice.csv"
    assert result.content_type == "text/csv"
    assert result.file_size_bytes == 1024
    assert result.extension == ".csv"


def test_valid_txt_metadata_is_accepted() -> None:
    result = validate_upload_metadata(
        original_filename="notes.txt",
        content_type="text/plain",
        file_size_bytes=1024,
    )

    assert result.original_filename == "notes.txt"
    assert result.content_type == "text/plain"
    assert result.file_size_bytes == 1024
    assert result.extension == ".txt"


def test_valid_pdf_metadata_is_accepted() -> None:
    result = validate_upload_metadata(
        original_filename="receipt.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
    )

    assert result.original_filename == "receipt.pdf"
    assert result.content_type == "application/pdf"
    assert result.file_size_bytes == 1024
    assert result.extension == ".pdf"


def test_surrounding_whitespace_in_filename_is_trimmed() -> None:
    result = validate_upload_metadata(
        original_filename="  receipt.pdf  ",
        content_type="application/pdf",
        file_size_bytes=1024,
    )

    assert result.original_filename == "receipt.pdf"


@pytest.mark.parametrize("filename", ["", "   "])
def test_blank_or_whitespace_only_filename_is_rejected(filename: str) -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename=filename,
            content_type="application/pdf",
            file_size_bytes=1024,
        )


def test_filename_with_forward_slash_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="uploads/receipt.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
        )


def test_filename_with_backslash_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename=r"uploads\receipt.pdf",
            content_type="application/pdf",
            file_size_bytes=1024,
        )


@pytest.mark.parametrize(
    "filename",
    ["../receipt.pdf", "..\\receipt.pdf", "receipt..pdf"],
)
def test_filename_with_path_traversal_is_rejected(filename: str) -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename=filename,
            content_type="application/pdf",
            file_size_bytes=1024,
        )


@pytest.mark.parametrize("filename", ["receipt", ".env", "receipt."])
def test_extensionless_or_hidden_filename_is_rejected(filename: str) -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename=filename,
            content_type="text/plain",
            file_size_bytes=1024,
        )


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="receipt.exe",
            content_type="application/pdf",
            file_size_bytes=1024,
        )


def test_unsupported_content_type_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="receipt.pdf",
            content_type="application/octet-stream",
            file_size_bytes=1024,
        )


def test_mismatched_extension_content_type_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="receipt.pdf",
            content_type="text/plain",
            file_size_bytes=1024,
        )


@pytest.mark.parametrize("file_size_bytes", [0, -1])
def test_non_positive_file_size_is_rejected(file_size_bytes: int) -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="receipt.pdf",
            content_type="application/pdf",
            file_size_bytes=file_size_bytes,
        )


def test_file_larger_than_max_size_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        validate_upload_metadata(
            original_filename="receipt.pdf",
            content_type="application/pdf",
            file_size_bytes=MAX_UPLOAD_SIZE_BYTES + 1,
        )


def test_file_exactly_at_max_size_is_accepted() -> None:
    result = validate_upload_metadata(
        original_filename="receipt.pdf",
        content_type="application/pdf",
        file_size_bytes=MAX_UPLOAD_SIZE_BYTES,
    )

    assert result.file_size_bytes == MAX_UPLOAD_SIZE_BYTES


def test_allowed_extension_matching_is_case_insensitive() -> None:
    result = validate_upload_metadata(
        original_filename="receipt.PDF",
        content_type="application/pdf",
        file_size_bytes=1024,
    )

    assert result.original_filename == "receipt.PDF"
    assert result.extension == ".pdf"


def test_returned_validation_result_includes_safe_metadata() -> None:
    result = validate_upload_metadata(
        original_filename="report.CSV",
        content_type="text/csv",
        file_size_bytes=2048,
    )

    assert result.original_filename == "report.CSV"
    assert result.content_type == "text/csv"
    assert result.file_size_bytes == 2048
    assert result.extension == ".csv"


def test_validation_performs_no_file_io(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_open(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("validation must not open files")

    monkeypatch.setattr(builtins, "open", fail_open)
    before_paths = set(tmp_path.iterdir())

    result = validate_upload_metadata(
        original_filename="receipt.pdf",
        content_type="application/pdf",
        file_size_bytes=1024,
    )

    after_paths = set(tmp_path.iterdir())
    assert result.original_filename == "receipt.pdf"
    assert after_paths == before_paths
