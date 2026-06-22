"""Tests for the Vault user ORM model."""

from __future__ import annotations

from typing import cast

from sqlalchemy import Boolean, DateTime, String, Uuid
from sqlalchemy.schema import Index, Table, UniqueConstraint

from vault.auth.models import User
from vault.models import Base


def test_user_model_table_name() -> None:
    assert User.__tablename__ == "users"


def test_user_model_has_expected_columns() -> None:
    columns = User.__table__.columns

    assert set(columns.keys()) == {
        "id",
        "email",
        "password_hash",
        "full_name",
        "is_active",
        "created_at",
    }
    assert isinstance(columns["id"].type, Uuid)
    assert isinstance(columns["email"].type, String)
    assert isinstance(columns["password_hash"].type, String)
    assert isinstance(columns["full_name"].type, String)
    assert isinstance(columns["is_active"].type, Boolean)
    assert isinstance(columns["created_at"].type, DateTime)


def test_user_model_column_lengths_are_reasonable() -> None:
    columns = User.__table__.columns

    assert cast(String, columns["email"].type).length == 320
    assert cast(String, columns["password_hash"].type).length == 255
    assert cast(String, columns["full_name"].type).length == 120


def test_required_user_columns_are_not_nullable() -> None:
    for column in User.__table__.columns:
        assert column.nullable is False


def test_user_email_has_uniqueness_rule() -> None:
    table = cast(Table, User.__table__)
    unique_columns = {
        column.name
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
        for column in constraint.columns
    }
    unique_index_columns = {
        column.name
        for index in table.indexes
        if isinstance(index, Index) and index.unique
        for column in index.columns
    }

    assert "email" in unique_columns | unique_index_columns


def test_model_metadata_includes_users_table() -> None:
    assert "users" in Base.metadata.tables
    assert Base.metadata.tables["users"] is User.__table__
