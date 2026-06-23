"""Shared FastAPI dependencies for Vault routes."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from vault.database import (
    create_engine_from_environment,
    create_session_factory,
)


def get_database_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session and close it safely after the request."""
    engine = create_engine_from_environment()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session
