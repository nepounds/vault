"""Tests for Vault user creation service behavior."""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.passwords import verify_password
from vault.auth.service import create_user
from vault.exceptions import DuplicateUserError, ValidationError
from vault.models import Base


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with session_factory() as test_session:
        yield test_session


def test_create_user_stores_normalized_email(session: Session) -> None:
    user = create_user(
        session,
        email="  PERSON@Example.COM  ",
        raw_password="safe password",
        full_name="Person Example",
    )

    assert user.email == "person@example.com"


def test_create_user_stores_full_name(session: Session) -> None:
    user = create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name=" Person Example ",
    )

    assert user.full_name == "Person Example"


def test_create_user_sets_is_active_true(session: Session) -> None:
    user = create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )

    assert user.is_active is True


def test_create_user_stores_password_hash_not_raw_password(
    session: Session,
) -> None:
    raw_password = "safe password"

    user = create_user(
        session,
        email="person@example.com",
        raw_password=raw_password,
        full_name="Person Example",
    )

    assert user.password_hash != raw_password


def test_create_user_password_hash_verifies_original_password(
    session: Session,
) -> None:
    raw_password = "safe password"

    user = create_user(
        session,
        email="person@example.com",
        raw_password=raw_password,
        full_name="Person Example",
    )

    assert verify_password(raw_password, user.password_hash) is True


def test_create_user_rejects_blank_email(session: Session) -> None:
    with pytest.raises(ValidationError, match="email is required"):
        create_user(
            session,
            email="   ",
            raw_password="safe password",
            full_name="Person Example",
        )


def test_create_user_rejects_blank_password(session: Session) -> None:
    with pytest.raises(ValidationError, match="password is required"):
        create_user(
            session,
            email="person@example.com",
            raw_password="   ",
            full_name="Person Example",
        )


def test_create_user_rejects_blank_full_name(session: Session) -> None:
    with pytest.raises(ValidationError, match="full_name is required"):
        create_user(
            session,
            email="person@example.com",
            raw_password="safe password",
            full_name="   ",
        )


def test_create_user_rejects_duplicate_normalized_email(
    session: Session,
) -> None:
    create_user(
        session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )

    with pytest.raises(DuplicateUserError, match="email already exists"):
        create_user(
            session,
            email="  PERSON@example.com  ",
            raw_password="another safe password",
            full_name="Another Person",
        )
