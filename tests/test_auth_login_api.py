"""Tests for the Vault login API."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
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


def login_payload(
    *,
    email: str = "Person@Example.COM",
    password: str = "safe password",
) -> dict[str, str]:
    """Build a valid login payload with optional overrides."""
    return {"email": email, "password": password}


def create_login_user(db_session: Session) -> User:
    """Create a default active user for login API tests."""
    user = create_user(
        db_session,
        email="person@example.com",
        raw_password="safe password",
        full_name="Person Example",
    )
    db_session.commit()
    return user


def test_login_returns_success_status(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 200


def test_successful_login_returns_access_token(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 200
    assert isinstance(response.json()["access_token"], str)
    assert response.json()["access_token"] != ""


def test_successful_login_returns_bearer_token_type(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


def test_login_response_does_not_include_password(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 200
    assert "password" not in response.json()


def test_login_response_does_not_include_password_hash(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 200
    assert "password_hash" not in response.json()


def test_wrong_password_returns_unauthorized(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)

    response = client.post(
        "/auth/login",
        json=login_payload(password="wrong password"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_unknown_email_returns_unauthorized(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        json=login_payload(email="missing@example.com"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."


def test_inactive_user_login_returns_forbidden(
    client: TestClient,
    db_session: Session,
) -> None:
    create_login_user(db_session)
    user = db_session.scalar(select(User).where(User.email == "person@example.com"))
    assert user is not None
    user.is_active = False
    db_session.commit()

    response = client.post("/auth/login", json=login_payload())

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid email or password."


@pytest.mark.parametrize(
    ("field_name", "blank_value"),
    [
        ("email", "   "),
        ("password", "   "),
    ],
)
def test_login_rejects_blank_required_fields(
    client: TestClient,
    field_name: str,
    blank_value: str,
) -> None:
    payload = login_payload()
    payload[field_name] = blank_value

    response = client.post("/auth/login", json=payload)

    assert response.status_code == 422


def test_openapi_schema_includes_login_path(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/auth/login" in response.json()["paths"]
