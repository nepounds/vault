"""Tests for the Vault registration API."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.auth.models import User
from vault.auth.passwords import verify_password
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
    """Open a database session for inspecting API side effects."""
    with session_factory() as test_session:
        yield test_session


def register_payload(
    *,
    email: str = "Person@Example.COM",
    password: str = "safe password",
    full_name: str = "Person Example",
) -> dict[str, str]:
    """Build a valid registration payload with optional overrides."""
    return {
        "email": email,
        "password": password,
        "full_name": full_name,
    }


def test_registration_returns_created_status(client: TestClient) -> None:
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201


def test_registration_returns_safe_user_fields(client: TestClient) -> None:
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "id",
        "email",
        "full_name",
        "is_active",
        "created_at",
    }
    assert body["email"] == "person@example.com"
    assert body["full_name"] == "Person Example"
    assert body["is_active"] is True


def test_registration_does_not_return_password(client: TestClient) -> None:
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201
    assert "password" not in response.json()


def test_registration_does_not_return_password_hash(client: TestClient) -> None:
    response = client.post("/auth/register", json=register_payload())

    assert response.status_code == 201
    assert "password_hash" not in response.json()


def test_registration_normalizes_email(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json=register_payload(email="  PERSON@Example.COM  "),
    )

    assert response.status_code == 201
    assert response.json()["email"] == "person@example.com"


def test_registration_stores_password_hash_not_raw_password(
    client: TestClient,
    db_session: Session,
) -> None:
    raw_password = "safe password"

    response = client.post(
        "/auth/register",
        json=register_payload(password=raw_password),
    )

    assert response.status_code == 201
    user = db_session.scalar(select(User).where(User.email == "person@example.com"))
    assert user is not None
    assert user.password_hash != raw_password
    assert verify_password(raw_password, user.password_hash) is True


@pytest.mark.parametrize(
    ("field_name", "blank_value"),
    [
        ("email", "   "),
        ("password", "   "),
        ("full_name", "   "),
    ],
)
def test_registration_rejects_blank_required_fields(
    client: TestClient,
    field_name: str,
    blank_value: str,
) -> None:
    payload = register_payload()
    payload[field_name] = blank_value

    response = client.post("/auth/register", json=payload)

    assert response.status_code == 422


def test_registration_rejects_duplicate_normalized_email(
    client: TestClient,
) -> None:
    first_response = client.post(
        "/auth/register",
        json=register_payload(email="person@example.com"),
    )

    second_response = client.post(
        "/auth/register",
        json=register_payload(email="  PERSON@example.com  "),
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "A user with this email already exists."
    )


def test_openapi_schema_includes_registration_path(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/auth/register" in response.json()["paths"]


def test_registration_creates_user_registered_audit_entry(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/auth/register",
        json=register_payload(password="very safe password"),
    )

    assert response.status_code == 201
    audit_entry = db_session.scalar(select(AuditEntry))
    assert audit_entry is not None
    assert audit_entry.action == AuditAction.USER_REGISTERED.value
    assert audit_entry.entity_type == AuditEntityType.USER.value
    assert audit_entry.organization_id is None
    assert audit_entry.entity_id == audit_entry.actor_user_id
    assert audit_entry.metadata_json["email"] == "person@example.com"
    assert audit_entry.metadata_json["actor_user_id_policy"] == "created_user"


def test_registration_audit_entry_omits_password_data(
    client: TestClient,
    db_session: Session,
) -> None:
    raw_password = "very safe password"
    response = client.post(
        "/auth/register",
        json=register_payload(password=raw_password),
    )

    assert response.status_code == 201
    user = db_session.scalar(select(User).where(User.email == "person@example.com"))
    audit_entry = db_session.scalar(select(AuditEntry))
    assert user is not None
    assert audit_entry is not None
    metadata_text = str(audit_entry.metadata_json)
    assert raw_password not in metadata_text
    assert user.password_hash not in metadata_text
    assert "password" not in metadata_text.lower()
    assert "token" not in metadata_text.lower()


def test_failed_registration_validation_does_not_create_audit_entry(
    client: TestClient,
    db_session: Session,
) -> None:
    response = client.post(
        "/auth/register",
        json=register_payload(email=" "),
    )

    assert response.status_code == 422
    assert db_session.scalars(select(AuditEntry)).all() == []
