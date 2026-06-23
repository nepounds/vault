"""Tests for Vault login service behavior."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.service import authenticate_user, create_user
from vault.exceptions import AuthenticationError, InactiveUserError
from vault.models import Base


@pytest.fixture
def session() -> Iterator[Session]:
    """Create an isolated SQLite session for service tests."""
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as test_session:
        yield test_session


def test_login_succeeds_with_normalized_email_and_correct_password(
    session: Session,
) -> None:
    created_user = create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )

    authenticated_user = authenticate_user(
        session,
        email="  PERSON@Example.COM  ",
        raw_password="safe password",
    )

    assert authenticated_user.id == created_user.id


def test_login_fails_with_wrong_password(session: Session) -> None:
    create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )

    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(
            session,
            email="person@example.com",
            raw_password="wrong password",
        )


def test_login_fails_with_unknown_email(session: Session) -> None:
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        authenticate_user(
            session,
            email="missing@example.com",
            raw_password="safe password",
        )


def test_login_fails_for_inactive_users(session: Session) -> None:
    user = create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )
    user.is_active = False
    session.flush()

    with pytest.raises(InactiveUserError, match="Inactive users cannot log in"):
        authenticate_user(
            session,
            email="person@example.com",
            raw_password="safe password",
        )


def test_login_result_does_not_expose_password_values(session: Session) -> None:
    create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )

    authenticated_user = authenticate_user(
        session,
        email="person@example.com",
        raw_password="safe password",
    )

    assert hasattr(authenticated_user, "password") is False
    assert hasattr(authenticated_user, "password_hash") is False
