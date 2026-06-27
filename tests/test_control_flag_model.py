"""Tests for Vault control flag ORM model metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.schema import Index, Table

from vault.controls.models import ControlFlag
from vault.controls.severities import SEVERITY_VALUES, ControlFlagSeverity
from vault.controls.types import FLAG_TYPE_VALUES, ControlFlagType
from vault.models import Base


def test_control_flag_model_table_name() -> None:
    assert ControlFlag.__tablename__ == "control_flags"


def test_control_flag_model_has_expected_columns() -> None:
    columns = ControlFlag.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "document_id",
        "flag_type",
        "severity",
        "reason",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["document_id"].type, Uuid)
    assert isinstance(columns["flag_type"].type, String)
    assert isinstance(columns["severity"].type, String)
    assert isinstance(columns["reason"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_control_flag_column_lengths_are_reasonable() -> None:
    columns = ControlFlag.__table__.columns

    assert cast(String, columns["flag_type"].type).length == 80
    assert cast(String, columns["severity"].type).length == 20
    assert cast(String, columns["reason"].type).length == 500


def test_control_flag_id_is_uuid_primary_key() -> None:
    id_column = ControlFlag.__table__.columns["id"]

    assert isinstance(id_column.type, Uuid)
    assert id_column.primary_key is True


def test_required_control_flag_columns_are_not_nullable() -> None:
    columns = ControlFlag.__table__.columns

    assert columns["id"].nullable is False
    assert columns["document_id"].nullable is False
    assert columns["flag_type"].nullable is False
    assert columns["severity"].nullable is False
    assert columns["reason"].nullable is False
    assert columns["created_at"].nullable is False


def test_control_flag_has_foreign_key_to_documents() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, ControlFlag.__table__))

    assert "documents.id" in foreign_key_targets


def test_control_flag_created_at_uses_utc_aware_default() -> None:
    default = ControlFlag.__table__.columns["created_at"].default

    assert default is not None
    default_callable = cast(Callable[[object], datetime], default.arg)
    created_at = default_callable(None)

    assert created_at.tzinfo is UTC


def test_official_control_flag_severity_values_exist() -> None:
    assert SEVERITY_VALUES == ("info", "warning", "blocker")
    assert ControlFlagSeverity.INFO.value == "info"
    assert ControlFlagSeverity.WARNING.value == "warning"
    assert ControlFlagSeverity.BLOCKER.value == "blocker"


def test_official_control_flag_type_values_exist() -> None:
    assert FLAG_TYPE_VALUES == (
        "missing_invoice_number",
        "missing_invoice_date",
        "missing_due_date",
        "non_usd_currency",
        "high_amount",
        "duplicate_file_hash",
        "duplicate_invoice_attributes",
    )
    assert ControlFlagType.MISSING_INVOICE_NUMBER.value == "missing_invoice_number"
    assert ControlFlagType.MISSING_INVOICE_DATE.value == "missing_invoice_date"
    assert ControlFlagType.MISSING_DUE_DATE.value == "missing_due_date"
    assert ControlFlagType.NON_USD_CURRENCY.value == "non_usd_currency"
    assert ControlFlagType.HIGH_AMOUNT.value == "high_amount"
    assert ControlFlagType.DUPLICATE_FILE_HASH.value == "duplicate_file_hash"
    assert (
        ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value
        == "duplicate_invoice_attributes"
    )


def test_control_flag_severity_check_constraint_exists() -> None:
    check_constraints = _check_constraints(cast(Table, ControlFlag.__table__))

    assert any(
        constraint.name == "ck_control_flags_severity_valid"
        and "severity IN" in str(constraint.sqltext)
        and "'info'" in str(constraint.sqltext)
        and "'warning'" in str(constraint.sqltext)
        and "'blocker'" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_control_flag_type_check_constraint_exists() -> None:
    check_constraints = _check_constraints(cast(Table, ControlFlag.__table__))

    assert any(
        constraint.name == "ck_control_flags_flag_type_valid"
        and "flag_type IN" in str(constraint.sqltext)
        and "'missing_invoice_number'" in str(constraint.sqltext)
        and "'duplicate_invoice_attributes'" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_control_flag_lookup_indexes_exist() -> None:
    indexed_column_sets = _indexed_column_sets(cast(Table, ControlFlag.__table__))

    assert ("document_id",) in indexed_column_sets
    assert ("severity",) in indexed_column_sets
    assert ("flag_type",) in indexed_column_sets


def test_control_flag_document_severity_composite_index_exists() -> None:
    indexed_column_sets = _indexed_column_sets(cast(Table, ControlFlag.__table__))

    assert ("document_id", "severity") in indexed_column_sets


def test_model_metadata_includes_control_flags() -> None:
    assert "control_flags" in Base.metadata.tables
    assert Base.metadata.tables["control_flags"] is ControlFlag.__table__


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
