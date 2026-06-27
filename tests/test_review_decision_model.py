"""Tests for Vault review decision ORM model metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import CheckConstraint, DateTime, Index, String, Table, Uuid
from sqlalchemy.schema import ColumnDefault

from vault.models import Base
from vault.reviews.decisions import DECISION_VALUES, ReviewDecisionValueEnum
from vault.reviews.models import ReviewDecision


def _review_decision_table() -> Table:
    return cast(Table, ReviewDecision.__table__)


def test_review_decision_model_table_name() -> None:
    assert ReviewDecision.__tablename__ == "review_decisions"


def test_review_decision_model_has_expected_columns() -> None:
    table = _review_decision_table()
    columns = table.columns

    assert set(columns.keys()) == {
        "id",
        "document_id",
        "reviewer_user_id",
        "decision",
        "reason",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["document_id"].type, Uuid)
    assert isinstance(columns["reviewer_user_id"].type, Uuid)
    assert isinstance(columns["decision"].type, String)
    assert isinstance(columns["reason"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_review_decision_column_lengths_are_reasonable() -> None:
    table = _review_decision_table()
    columns = table.columns

    assert cast(String, columns["decision"].type).length == 30
    assert cast(String, columns["reason"].type).length == 500


def test_review_decision_id_is_uuid_primary_key() -> None:
    table = _review_decision_table()
    id_column = table.columns["id"]

    assert isinstance(id_column.type, Uuid)
    assert id_column.primary_key is True


def test_required_review_decision_columns_are_not_nullable() -> None:
    table = _review_decision_table()
    columns = table.columns

    assert columns["id"].nullable is False
    assert columns["document_id"].nullable is False
    assert columns["reviewer_user_id"].nullable is False
    assert columns["decision"].nullable is False
    assert columns["reason"].nullable is False
    assert columns["created_at"].nullable is False


def test_review_decision_has_foreign_key_to_documents() -> None:
    foreign_key_targets = _foreign_key_targets(_review_decision_table())

    assert "documents.id" in foreign_key_targets


def test_review_decision_has_foreign_key_to_users() -> None:
    foreign_key_targets = _foreign_key_targets(_review_decision_table())

    assert "users.id" in foreign_key_targets


def test_review_decision_created_at_uses_utc_aware_default() -> None:
    table = _review_decision_table()
    default = table.columns["created_at"].default

    assert default is not None
    column_default = cast(ColumnDefault, default)
    default_callable = cast(Callable[[object], datetime], column_default.arg)
    created_at = default_callable(None)

    assert created_at.tzinfo is UTC


def test_official_review_decision_values_exist() -> None:
    assert DECISION_VALUES == ("approved", "rejected", "needs_info")
    assert ReviewDecisionValueEnum.APPROVED.value == "approved"
    assert ReviewDecisionValueEnum.REJECTED.value == "rejected"
    assert ReviewDecisionValueEnum.NEEDS_INFO.value == "needs_info"


def test_pending_is_not_an_official_review_decision() -> None:
    assert "pending" not in DECISION_VALUES


def test_review_decision_check_constraint_exists() -> None:
    check_constraints = _check_constraints(_review_decision_table())

    assert any(
        constraint.name == "ck_review_decisions_decision_valid"
        and "decision IN" in str(constraint.sqltext)
        and "'approved'" in str(constraint.sqltext)
        and "'rejected'" in str(constraint.sqltext)
        and "'needs_info'" in str(constraint.sqltext)
        and "'pending'" not in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_review_decision_lookup_indexes_exist() -> None:
    indexed_column_sets = _indexed_column_sets(_review_decision_table())

    assert ("document_id",) in indexed_column_sets
    assert ("reviewer_user_id",) in indexed_column_sets
    assert ("decision",) in indexed_column_sets


def test_review_decision_document_created_at_composite_index_exists() -> None:
    indexed_column_sets = _indexed_column_sets(_review_decision_table())

    assert ("document_id", "created_at") in indexed_column_sets


def test_review_decision_has_no_uniqueness_constraint() -> None:
    table = _review_decision_table()
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ]

    assert unique_constraints == []


def test_model_metadata_includes_review_decisions() -> None:
    table = _review_decision_table()

    assert "review_decisions" in Base.metadata.tables
    assert Base.metadata.tables["review_decisions"] is table


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