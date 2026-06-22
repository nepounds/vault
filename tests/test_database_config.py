"""Tests for SQLAlchemy database configuration helpers."""

from __future__ import annotations

from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from vault.config import VaultSettings
from vault.database import (
    create_database_engine,
    create_engine_from_settings,
    create_session_factory,
)


def test_create_database_engine_does_not_connect_immediately() -> None:
    """Creating an engine should not require a live database connection."""
    engine = create_database_engine("sqlite+pysqlite:///:memory:")

    assert isinstance(engine, Engine)
    assert engine.url.database == ":memory:"


def test_create_session_factory_from_engine() -> None:
    """A SQLAlchemy session factory can be created from an engine."""
    engine = create_database_engine("sqlite+pysqlite:///:memory:")
    session_factory = create_session_factory(engine)

    assert isinstance(session_factory, sessionmaker)

    session = session_factory()
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_create_engine_from_settings_uses_database_url() -> None:
    """Settings can provide the database URL used to create an engine."""
    settings = VaultSettings(database_url="sqlite+pysqlite:///:memory:")

    engine = create_engine_from_settings(settings)

    assert isinstance(engine, Engine)
    assert engine.url.database == ":memory:"
