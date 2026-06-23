"""Tests for Vault organization and membership ORM models."""

from __future__ import annotations

from typing import cast

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.schema import Index, Table, UniqueConstraint

from vault.models import Base
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import ROLE_VALUES, MembershipRole


def test_organization_model_table_name() -> None:
    assert Organization.__tablename__ == "organizations"


def test_membership_model_table_name() -> None:
    assert Membership.__tablename__ == "memberships"


def test_organization_model_has_expected_columns() -> None:
    columns = Organization.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "name",
        "created_by_user_id",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["name"].type, String)
    assert isinstance(columns["created_by_user_id"].type, Uuid)
    assert isinstance(columns["created_at"].type, DateTime)


def test_membership_model_has_expected_columns() -> None:
    columns = Membership.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "organization_id",
        "user_id",
        "role",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["organization_id"].type, Uuid)
    assert isinstance(columns["user_id"].type, Uuid)
    assert isinstance(columns["role"].type, String)
    assert isinstance(columns["created_at"].type, DateTime)


def test_organization_column_lengths_are_reasonable() -> None:
    columns = Organization.__table__.columns

    assert cast(String, columns["name"].type).length == 160


def test_membership_column_lengths_are_reasonable() -> None:
    columns = Membership.__table__.columns

    assert cast(String, columns["role"].type).length == 20


def test_required_organization_columns_are_not_nullable() -> None:
    for column in Organization.__table__.columns:
        assert column.nullable is False


def test_required_membership_columns_are_not_nullable() -> None:
    for column in Membership.__table__.columns:
        assert column.nullable is False


def test_organization_id_uses_uuid_style_metadata() -> None:
    assert isinstance(Organization.__table__.columns["id"].type, Uuid)


def test_membership_id_uses_uuid_style_metadata() -> None:
    assert isinstance(Membership.__table__.columns["id"].type, Uuid)


def test_role_values_include_exactly_owner_reviewer_and_viewer() -> None:
    assert ROLE_VALUES == ("owner", "reviewer", "viewer")
    assert {role.value for role in MembershipRole} == set(ROLE_VALUES)


def test_membership_role_column_has_check_constraint() -> None:
    table = cast(Table, Membership.__table__)
    check_constraints = [
        constraint
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint)
    ]

    assert any(
        constraint.name == "ck_memberships_role_valid"
        and "owner" in str(constraint.sqltext)
        and "reviewer" in str(constraint.sqltext)
        and "viewer" in str(constraint.sqltext)
        for constraint in check_constraints
    )


def test_membership_has_foreign_keys_to_users_and_organizations() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, Membership.__table__))

    assert "organizations.id" in foreign_key_targets
    assert "users.id" in foreign_key_targets


def test_organization_has_foreign_key_to_creator_user() -> None:
    foreign_key_targets = _foreign_key_targets(cast(Table, Organization.__table__))

    assert "users.id" in foreign_key_targets


def test_duplicate_membership_uniqueness_rule_exists() -> None:
    table = cast(Table, Membership.__table__)
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("organization_id", "user_id") in unique_column_sets


def test_membership_lookup_indexes_exist() -> None:
    table = cast(Table, Membership.__table__)
    indexed_column_sets = {
        tuple(column.name for column in index.columns)
        for index in table.indexes
        if isinstance(index, Index)
    }

    assert ("organization_id",) in indexed_column_sets
    assert ("user_id",) in indexed_column_sets


def test_model_metadata_includes_organizations_and_memberships() -> None:
    assert "organizations" in Base.metadata.tables
    assert "memberships" in Base.metadata.tables
    assert Base.metadata.tables["organizations"] is Organization.__table__
    assert Base.metadata.tables["memberships"] is Membership.__table__


def _foreign_key_targets(table: Table) -> set[str]:
    return {
        str(foreign_key.column)
        for column in table.columns
        for foreign_key in column.foreign_keys
    }
