"""Tests for Vault audit entry ORM model metadata."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from sqlalchemy import JSON, CheckConstraint, DateTime, Index, String, Table, Uuid
from sqlalchemy.schema import ColumnDefault

from vault.audit.actions import AUDIT_ACTION_VALUES, AuditAction
from vault.audit.entities import AUDIT_ENTITY_TYPE_VALUES, AuditEntityType
from vault.audit.models import AuditEntry
from vault.models import Base


def _audit_entry_table() -> Table:
    return cast(Table, AuditEntry.__table__)


def test_audit_entry_model_table_name() -> None:
    assert AuditEntry.__tablename__ == "audit_entries"


def test_audit_entry_model_has_expected_columns() -> None:
    table = _audit_entry_table()
    columns = table.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "actor_user_id",
        "action",
        "entity_type",
        "entity_id",
        "summary",
        "metadata_json",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["organization_id"].type, Uuid)
    assert isinstance(columns["actor_user_id"].type, Uuid)
    assert isinstance(columns["action"].type, String)
    assert isinstance(columns["entity_type"].type, String)
    assert isinstance(columns["entity_id"].type, Uuid)
    assert isinstance(columns["summary"].type, String)
    assert isinstance(columns["metadata_json"].type, JSON)
    assert isinstance(columns["created_at"].type, DateTime)


def test_audit_entry_column_lengths_are_reasonable() -> None:
    table = _audit_entry_table()
    columns = table.columns

    assert cast(String, columns["action"].type).length == 60
    assert cast(String, columns["entity_type"].type).length == 40
    assert cast(String, columns["summary"].type).length == 500


def test_audit_entry_id_is_uuid_primary_key() -> None:
    table = _audit_entry_table()
    id_column = table.columns["id"]

    assert isinstance(id_column.type, Uuid)
    assert id_column.primary_key is True


def test_audit_entry_nullable_columns_match_scope_rules() -> None:
    table = _audit_entry_table()
    columns = table.columns

    assert columns["organization_id"].nullable is True
    assert columns["actor_user_id"].nullable is True
    assert columns["entity_id"].nullable is True


def test_required_audit_entry_columns_are_not_nullable() -> None:
    table = _audit_entry_table()
    columns = table.columns

    assert columns["id"].nullable is False
    assert columns["action"].nullable is False
    assert columns["entity_type"].nullable is False
    assert columns["summary"].nullable is False
    assert columns["metadata_json"].nullable is False
    assert columns["created_at"].nullable is False


def test_audit_entry_has_foreign_key_to_organizations() -> None:
    foreign_key_targets = _foreign_key_targets(_audit_entry_table())

    assert "organizations.id" in foreign_key_targets


def test_audit_entry_has_foreign_key_to_users() -> None:
    foreign_key_targets = _foreign_key_targets(_audit_entry_table())

    assert "users.id" in foreign_key_targets


def test_audit_entry_entity_id_has_no_foreign_key() -> None:
    table = _audit_entry_table()

    assert table.columns["entity_id"].foreign_keys == set()


def test_audit_entry_metadata_json_uses_empty_dict_default() -> None:
    table = _audit_entry_table()
    default = table.columns["metadata_json"].default

    assert default is not None
    column_default = cast(ColumnDefault, default)
    default_callable = cast(Callable[[object], dict[str, object]], column_default.arg)

    assert default_callable(None) == {}
    assert default_callable(None) is not default_callable(None)


def test_audit_entry_created_at_uses_utc_aware_default() -> None:
    table = _audit_entry_table()
    default = table.columns["created_at"].default

    assert default is not None
    column_default = cast(ColumnDefault, default)
    default_callable = cast(Callable[[object], datetime], column_default.arg)
    created_at = default_callable(None)

    assert created_at.tzinfo is UTC


def test_official_audit_action_values_exist() -> None:
    assert AUDIT_ACTION_VALUES == (
        "user_registered",
        "organization_created",
        "document_uploaded",
        "document_fact_created",
        "control_flags_generated",
        "duplicate_flags_generated",
        "review_decision_created",
        "document_status_changed",
        "export_generated",
    )
    assert AuditAction.USER_REGISTERED.value == "user_registered"
    assert AuditAction.ORGANIZATION_CREATED.value == "organization_created"
    assert AuditAction.DOCUMENT_UPLOADED.value == "document_uploaded"
    assert AuditAction.DOCUMENT_FACT_CREATED.value == "document_fact_created"
    assert AuditAction.CONTROL_FLAGS_GENERATED.value == "control_flags_generated"
    assert AuditAction.DUPLICATE_FLAGS_GENERATED.value == "duplicate_flags_generated"
    assert AuditAction.REVIEW_DECISION_CREATED.value == "review_decision_created"
    assert AuditAction.DOCUMENT_STATUS_CHANGED.value == "document_status_changed"
    assert AuditAction.EXPORT_GENERATED.value == "export_generated"


def test_official_audit_entity_type_values_exist() -> None:
    assert AUDIT_ENTITY_TYPE_VALUES == (
        "user",
        "organization",
        "document",
        "document_fact",
        "control_flag",
        "review_decision",
        "export",
    )
    assert AuditEntityType.USER.value == "user"
    assert AuditEntityType.ORGANIZATION.value == "organization"
    assert AuditEntityType.DOCUMENT.value == "document"
    assert AuditEntityType.DOCUMENT_FACT.value == "document_fact"
    assert AuditEntityType.CONTROL_FLAG.value == "control_flag"
    assert AuditEntityType.REVIEW_DECISION.value == "review_decision"
    assert AuditEntityType.EXPORT.value == "export"


def test_audit_action_check_constraint_exists() -> None:
    check_constraints = _check_constraints(_audit_entry_table())

    assert any(
        constraint.name == "ck_audit_entries_action_valid"
        and "action IN" in str(constraint.sqltext)
        and "'user_registered'" in str(constraint.sqltext)
        and "'review_decision_created'" in str(constraint.sqltext)
        and "'export_generated'" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_audit_entity_type_check_constraint_exists() -> None:
    check_constraints = _check_constraints(_audit_entry_table())

    assert any(
        constraint.name == "ck_audit_entries_entity_type_valid"
        and "entity_type IN" in str(constraint.sqltext)
        and "'user'" in str(constraint.sqltext)
        and "'document'" in str(constraint.sqltext)
        and "'export'" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_audit_entry_lookup_indexes_exist() -> None:
    indexed_column_sets = _indexed_column_sets(_audit_entry_table())

    assert ("organization_id",) in indexed_column_sets
    assert ("actor_user_id",) in indexed_column_sets
    assert ("action",) in indexed_column_sets
    assert ("entity_type",) in indexed_column_sets
    assert ("created_at",) in indexed_column_sets


def test_audit_entry_organization_created_at_composite_index_exists() -> None:
    indexed_column_sets = _indexed_column_sets(_audit_entry_table())

    assert ("organization_id", "created_at") in indexed_column_sets


def test_audit_entry_entity_type_entity_id_composite_index_exists() -> None:
    indexed_column_sets = _indexed_column_sets(_audit_entry_table())

    assert ("entity_type", "entity_id") in indexed_column_sets


def test_audit_entry_has_no_uniqueness_constraint() -> None:
    table = _audit_entry_table()
    unique_constraints = [
        constraint
        for constraint in table.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    ]

    assert unique_constraints == []


def test_model_metadata_includes_audit_entries() -> None:
    table = _audit_entry_table()

    assert "audit_entries" in Base.metadata.tables
    assert Base.metadata.tables["audit_entries"] is table


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
