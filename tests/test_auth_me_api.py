"""Tests for the current-user auth API."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.models import Base


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for route tests."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def client(
    session_factory: sessionmaker[Session],
) -> Iterator[TestClient]:
    """Create a test client with the database dependency overridden."""
    app = create_app()

    def override_database_session() -> Iterator[Session]:
        with session_factory() as test_session:
            yield test_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Open a database session for arranging API test users."""
    with session_factory() as test_session:
        yield test_session


def create_me_user(db_session: Session) -> User:
    """Create a default user for /auth/me tests."""
    user = create_user(
        db_session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def test_me_without_token_returns_unauthorized(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_me_with_malformed_authorization_header_returns_unauthorized(
    client: TestClient,
) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Basic not-a-bearer-token"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_me_with_invalid_token_returns_unauthorized(client: TestClient) -> None:
    response = client.get("/auth/me", headers=auth_headers("not-a-token"))

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_me_with_expired_token_returns_unauthorized(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    current_time = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_access_token(
        user.id,
        expires_delta=timedelta(minutes=-1),
        now=current_time,
    )

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_me_with_valid_token_returns_success(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    token = create_access_token(user.id)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200


def test_me_returns_safe_user_fields(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    token = create_access_token(user.id)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert set(response.json()) == {
        "id",
        "email",
        "full_name",
        "is_active",
        "created_at",
    }
    assert response.json()["id"] == str(user.id)
    assert response.json()["email"] == "person@example.com"
    assert response.json()["full_name"] == "Person Example"
    assert response.json()["is_active"] is True


def test_me_does_not_return_password(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    token = create_access_token(user.id)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert "password" not in response.json()


def test_me_does_not_return_password_hash(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    token = create_access_token(user.id)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 200
    assert "password_hash" not in response.json()


def test_me_rejects_token_for_unknown_user(client: TestClient) -> None:
    token = create_access_token(uuid4())

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_me_rejects_inactive_user_token(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_me_user(db_session)
    user.is_active = False
    db_session.commit()
    token = create_access_token(user.id)

    response = client.get("/auth/me", headers=auth_headers(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_openapi_schema_includes_me_path(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/auth/me" in response.json()["paths"]
