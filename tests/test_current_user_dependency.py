"""Tests for current-user token resolution."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.api.dependencies import get_current_user
from vault.auth.models import User
from vault.auth.service import create_user, load_active_user_from_token
from vault.auth.tokens import create_access_token
from vault.exceptions import AuthenticationError, InactiveUserError
from vault.models import Base


@pytest.fixture
def session() -> Iterator[Session]:
    """Create an isolated SQLite session for dependency tests."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as test_session:
        yield test_session


def create_active_user(session: Session) -> User:
    """Create a default active user for current-user tests."""
    user = create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )
    session.commit()
    session.refresh(user)
    return user


def bearer_credentials(token: str) -> HTTPAuthorizationCredentials:
    """Build bearer credentials as FastAPI would after header parsing."""
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_missing_bearer_token_is_rejected(session: Session) -> None:
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, session=session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials."


def test_malformed_authorization_header_is_rejected(session: Session) -> None:
    credentials = HTTPAuthorizationCredentials(
        scheme="Basic",
        credentials="not-a-bearer-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=credentials, session=session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials."


def test_invalid_token_is_rejected(session: Session) -> None:
    with pytest.raises(AuthenticationError, match="Invalid access token"):
        load_active_user_from_token(session, "not-a-valid-token")


def test_expired_token_is_rejected(session: Session) -> None:
    user = create_active_user(session)
    current_time = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_access_token(
        user.id,
        expires_delta=timedelta(minutes=-1),
        now=current_time,
    )

    with pytest.raises(AuthenticationError, match="expired"):
        load_active_user_from_token(session, token)


def test_token_for_unknown_user_is_rejected(session: Session) -> None:
    token = create_access_token(uuid4())

    with pytest.raises(AuthenticationError, match="Invalid access token"):
        load_active_user_from_token(session, token)


def test_token_for_inactive_user_is_rejected(session: Session) -> None:
    user = create_active_user(session)
    user.is_active = False
    session.commit()
    token = create_access_token(user.id)

    with pytest.raises(InactiveUserError, match="Inactive users"):
        load_active_user_from_token(session, token)


def test_valid_token_resolves_expected_active_user(session: Session) -> None:
    user = create_active_user(session)
    token = create_access_token(user.id)

    current_user = get_current_user(
        credentials=bearer_credentials(token),
        session=session,
    )

    assert current_user.id == user.id
    assert current_user.email == "person@example.com"
