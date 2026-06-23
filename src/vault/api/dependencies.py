"""Shared FastAPI dependencies for Vault routes."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.auth.service import load_active_user_from_token
from vault.database import (
    create_engine_from_environment,
    create_session_factory,
)
from vault.exceptions import AuthenticationError

_bearer_scheme = HTTPBearer(auto_error=False)


def get_database_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session and close it safely after the request."""
    engine = create_engine_from_environment()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> User:
    """Return the active user identified by a valid bearer access token."""
    if credentials is None:
        raise _unauthorized_error()

    token = credentials.credentials.strip()
    if credentials.scheme.lower() != "bearer" or not token:
        raise _unauthorized_error()

    try:
        return load_active_user_from_token(session, token)
    except AuthenticationError as exc:
        raise _unauthorized_error() from exc


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
