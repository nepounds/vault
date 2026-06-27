"""Tests for Vault document fact ORM model metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, Date, DateTime, Integer, String, Uuid
from sqlalchemy.schema import Index, Table

from vault.documents.models import DocumentFact
from vault.models import Base


def test_document_fact_model_table_name() -> None:
    assert DocumentFact.__tablename__ == "document_facts"


def test_document_fact_model_has_expected_columns() -> None:
    columns = DocumentFact.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "document_id",
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "due_date",
        "amount_cents",
        "currency",
        "category",
        "memo",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["document_id"].type, Uuid)
    assert isinstance(columns["vendor_name"].type, String)
    assert isinstance(columns["invoice_number"].type, String)
    assert isinstance(columns["invoice_date"].type, Date)
    assert isinstance(columns["due_date"].type, Date)
    assert isinstance(columns["amount_cents"].type, Integer)
    assert isinstance(columns["currency"].type, String)
    assert isinstance(columns["category"].type, String)
    assert isinstance(columns["memo"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_document_fact_column_lengths_are_reasonable() -> None:
    columns = DocumentFact.__table__.columns

    assert cast(String, columns["vendor_name"].type).length == 255
    assert cast(String, columns["invoice_number"].type).length == 80
    assert cast(String, columns["currency"].type).length == 3
    assert cast(String, columns["category"].type).length == 120
    assert cast(String, columns["memo"].type).length == 500


def test_document_fact_id_is_uuid_primary_key() -> None:
    id_column = DocumentFact.__table__.columns["id"]

    assert isinstance(id_column.type, Uuid)
    assert id_column.primary_key is True


def test_required_document_fact_columns_are_not_nullable() -> None:
    columns = DocumentFact.__table__.columns

    assert columns["id"].nullable is False
    assert columns["document_id"].nullable is False
    assert columns["vendor_name"].nullable is False
    assert columns["amount_cents"].nullable is False
    assert columns["currency"].nullable is False
    assert columns["category"].nullable is False
    assert columns["created_at"].nullable is False


def test_optional_document_fact_columns_are_nullable() -> None:
    columns = DocumentFact.__table__.columns

    assert columns["invoice_number"].nullable is True
    assert columns["invoice_date"].nullable is True
    assert columns["due_date"].nullable is True
    assert columns["memo"].nullable is True


def test_document_fact_has_foreign_key_to_documents() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, DocumentFact.__table__))

    assert "documents.id" in foreign_key_targets


def test_document_fact_currency_default_is_usd() -> None:
    default = DocumentFact.__table__.columns["currency"].default

    assert default is not None
    assert default.arg == "USD"


def test_document_fact_created_at_uses_utc_aware_default() -> None:
    default = DocumentFact.__table__.columns["created_at"].default

    assert default is not None
    default_callable = cast(Callable[[object], datetime], default.arg)
    created_at = default_callable(None)

    assert created_at.tzinfo is UTC


def test_document_fact_amount_has_positive_check_constraint() -> None:
    check_constraints = _check_constraints(cast(Table, DocumentFact.__table__))

    assert any(
        constraint.name == "ck_document_facts_amount_positive"
        and "amount_cents > 0" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_document_fact_currency_has_uppercase_three_letter_constraint() -> None:
    check_constraints = _check_constraints(cast(Table, DocumentFact.__table__))

    assert any(
        constraint.name == "ck_document_facts_currency_uppercase_3"
        and "length(currency) = 3" in str(constraint.sqltext)
        and "currency = upper(currency)" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_document_fact_lookup_indexes_exist() -> None:
    indexed_column_sets = _indexed_column_sets(cast(Table, DocumentFact.__table__))

    assert ("document_id",) in indexed_column_sets
    assert ("vendor_name",) in indexed_column_sets
    assert ("invoice_number",) in indexed_column_sets


def test_document_fact_duplicate_detection_composite_index_exists() -> None:
    indexed_column_sets = _indexed_column_sets(cast(Table, DocumentFact.__table__))

    assert ("vendor_name", "invoice_number", "amount_cents") in indexed_column_sets


def test_model_metadata_includes_document_facts() -> None:
    assert "document_facts" in Base.metadata.tables
    assert Base.metadata.tables["document_facts"] is DocumentFact.__table__


def _check_constraints(table: Table) -> list[CheckConstraint]:
    return [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    ]


def _foreign_key_targets(table: Table) -> set[str]:
    return {
        str(foreign_key.column)
        for column in table.columns
        for foreign_key in column.foreign_keys
    }


def _indexed_column_sets(table: Table) -> set[tuple[str, ...]]:
    return {
        tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }
