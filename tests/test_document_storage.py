"""Tests for local document byte storage helpers."""

from __future__ import annotations

import builtins
import hashlib
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType

import pytest

import vault.documents.storage as storage_module
from vault.documents.storage import (
    calculate_sha256,
    generate_stored_filename,
    store_upload_bytes,
)
from vault.documents.validation import MAX_UPLOAD_SIZE_BYTES
from vault.exceptions import DocumentUploadValidationError


def test_calculate_sha256_returns_expected_lowercase_hex() -> None:
    digest = calculate_sha256(b"vault upload bytes")

    assert digest == hashlib.sha256(b"vault upload bytes").hexdigest()
    assert digest == digest.lower()


@pytest.mark.parametrize("extension", [".csv", ".txt", ".pdf"])
def test_generated_stored_filename_preserves_allowed_extension(
    extension: str,
) -> None:
    stored_filename = generate_stored_filename(extension)

    assert stored_filename.endswith(extension)


def test_generated_stored_filename_does_not_include_original_filename_text() -> None:
    stored_filename = generate_stored_filename(".csv")

    assert "invoice" not in stored_filename
    assert "receipt" not in stored_filename
    assert "customer" not in stored_filename


def test_generated_stored_filename_has_no_path_separators() -> None:
    stored_filename = generate_stored_filename(".pdf")

    assert "/" not in stored_filename
    assert "\\" not in stored_filename


def test_unsupported_extension_is_rejected() -> None:
    with pytest.raises(DocumentUploadValidationError):
        generate_stored_filename(".exe")


@pytest.mark.parametrize("extension", ["", "csv", ".", "..csv", ".CSV", "./csv"])
def test_malformed_extension_is_rejected(extension: str) -> None:
    with pytest.raises(DocumentUploadValidationError):
        generate_stored_filename(extension)


def test_store_upload_bytes_creates_upload_directory_if_missing(
    tmp_path: Path,
) -> None:
    upload_dir = tmp_path / "missing" / "uploads"

    result = store_upload_bytes(upload_dir, b"hello", ".txt")

    assert upload_dir.is_dir()
    assert result.stored_path.exists()


def test_store_upload_bytes_writes_expected_bytes(tmp_path: Path) -> None:
    result = store_upload_bytes(tmp_path, b"expected bytes", ".txt")

    assert result.stored_path.read_bytes() == b"expected bytes"


def test_store_upload_bytes_returns_stored_filename(tmp_path: Path) -> None:
    result = store_upload_bytes(tmp_path, b"data", ".csv")

    assert result.stored_filename.endswith(".csv")
    assert result.stored_filename == result.stored_path.name


def test_store_upload_bytes_returns_full_stored_path(tmp_path: Path) -> None:
    result = store_upload_bytes(tmp_path, b"data", ".pdf")

    assert result.stored_path == tmp_path / result.stored_filename


def test_store_upload_bytes_returns_file_size(tmp_path: Path) -> None:
    result = store_upload_bytes(tmp_path, b"12345", ".txt")

    assert result.file_size_bytes == 5


def test_store_upload_bytes_returns_sha256_hash(tmp_path: Path) -> None:
    result = store_upload_bytes(tmp_path, b"hash me", ".txt")

    assert result.sha256_hash == calculate_sha256(b"hash me")


def test_store_upload_bytes_rejects_empty_bytes(tmp_path: Path) -> None:
    with pytest.raises(DocumentUploadValidationError):
        store_upload_bytes(tmp_path, b"", ".txt")


def test_store_upload_bytes_rejects_oversized_bytes(tmp_path: Path) -> None:
    oversized_data = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    with pytest.raises(DocumentUploadValidationError):
        store_upload_bytes(tmp_path, oversized_data, ".txt")


def test_store_upload_bytes_does_not_write_outside_upload_directory(
    tmp_path: Path,
) -> None:
    upload_dir = tmp_path / "uploads"

    result = store_upload_bytes(upload_dir, b"safe", ".csv")

    assert result.stored_path.parent.resolve(strict=False) == upload_dir.resolve(
        strict=False,
    )
    assert result.stored_path.read_bytes() == b"safe"
    assert not (tmp_path / result.stored_filename).exists()


def test_filename_collision_fails_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedUuid:
        hex = "0" * 32

    monkeypatch.setattr(storage_module, "uuid4", lambda: FixedUuid())
    existing_path = tmp_path / f"{FixedUuid.hex}.pdf"
    existing_path.write_bytes(b"existing")

    with pytest.raises(FileExistsError):
        store_upload_bytes(tmp_path, b"new", ".pdf")

    assert existing_path.read_bytes() == b"existing"


def test_helpers_do_not_require_fastapi() -> None:
    module = storage_module

    assert isinstance(module, ModuleType)
    assert "fastapi" not in module.__dict__


def test_helpers_do_not_require_database(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_import(
        name: str,
        globals: Mapping[str, object] | None = None,
        locals: Mapping[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name.startswith("sqlalchemy"):
            raise AssertionError("storage helpers must not import SQLAlchemy")
        return original_import(name, globals, locals, fromlist, level)

    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", fail_import)

    assert calculate_sha256(b"database-free")
