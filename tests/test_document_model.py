"""Tests for Vault document ORM model metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Uuid
from sqlalchemy.schema import Index, Table

from vault.documents.models import Document
from vault.documents.statuses import STATUS_VALUES, DocumentStatus
from vault.models import Base


def test_document_model_table_name() -> None:
    assert Document.__tablename__ == "documents"


def test_document_model_has_expected_columns() -> None:
    columns = Document.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "uploaded_by_user_id",
        "original_filename",
        "stored_filename",
        "content_type",
        "file_size_bytes",
        "sha256_hash",
        "status",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["organization_id"].type, Uuid)
    assert isinstance(columns["uploaded_by_user_id"].type, Uuid)
    assert isinstance(columns["original_filename"].type, String)
    assert isinstance(columns["stored_filename"].type, String)
    assert isinstance(columns["content_type"].type, String)
    assert isinstance(columns["file_size_bytes"].type, Integer)
    assert isinstance(columns["sha256_hash"].type, String)
    assert isinstance(columns["status"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_document_column_lengths_are_reasonable() -> None:
    columns = Document.__table__.columns

    assert cast(String, columns["original_filename"].type).length == 255
    assert cast(String, columns["stored_filename"].type).length == 255
    assert cast(String, columns["content_type"].type).length == 120
    assert cast(String, columns["sha256_hash"].type).length == 64
    assert cast(String, columns["status"].type).length == 20


def test_required_document_columns_are_not_nullable() -> None:
    for column in Document.__table__.columns:
        assert column.nullable is False


def test_document_id_uses_uuid_style_metadata() -> None:
    assert isinstance(Document.__table__.columns["id"].type, Uuid)


def test_document_created_at_uses_utc_aware_default() -> None:
    default = Document.__table__.columns["created_at"].default

    assert default is not None
    default_callable = cast(Callable[[object], datetime], default.arg)
    created_at = default_callable(None)

    assert created_at.tzinfo is UTC


def test_document_status_values_are_exactly_official_values() -> None:
    assert STATUS_VALUES == ("pending", "approved", "rejected", "needs_info")
    assert {status.value for status in DocumentStatus} == set(STATUS_VALUES)


def test_document_status_default_is_pending() -> None:
    default = Document.__table__.columns["status"].default

    assert default is not None
    assert default.arg == "pending"


def test_document_status_column_has_check_constraint() -> None:
    table = cast(Table, Document.__table__)
    check_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert any(
        constraint.name == "ck_documents_status_valid"
        and "pending" in str(constraint.sqltext)
        and "approved" in str(constraint.sqltext)
        and "rejected" in str(constraint.sqltext)
        and "needs_info" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_document_has_foreign_key_to_organizations() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, Document.__table__))

    assert "organizations.id" in foreign_key_targets


def test_document_has_foreign_key_to_uploader_user() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, Document.__table__))

    assert "users.id" in foreign_key_targets


def test_document_lookup_indexes_exist() -> None:
    table = cast(Table, Document.__table__)
    indexed_column_sets = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert ("organization_id",) in indexed_column_sets
    assert ("organization_id", "status") in indexed_column_sets
    assert ("sha256_hash",) in indexed_column_sets


def test_model_metadata_includes_documents() -> None:
    assert "documents" in Base.metadata.tables
    assert Base.metadata.tables["documents"] is Document.__table__


def _foreign_key_targets(table: Table) -> set[str]:
    return {
        str(foreign_key.column)
        for column in table.columns
        for foreign_key in column.foreign_keys
    }
