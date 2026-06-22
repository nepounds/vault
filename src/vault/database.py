"""Database engine and session configuration helpers for Vault."""

from __future__ import annotations

from collections.abc import Mapping

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.config import VaultSettings, load_settings

SessionFactory = sessionmaker[Session]


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine without opening a database connection."""
    return create_engine(database_url, future=True)


def create_session_factory(engine: Engine) -> SessionFactory:
    """Create a SQLAlchemy session factory for the provided engine."""
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


def create_engine_from_settings(settings: VaultSettings) -> Engine:
    """Create a SQLAlchemy engine from typed Vault settings."""
    return create_database_engine(settings.database_url)


def create_engine_from_environment(
    environ: Mapping[str, str] | None = None,
) -> Engine:
    """Create a SQLAlchemy engine from environment-based settings."""
    settings = load_settings(environ)
    return create_engine_from_settings(settings)
