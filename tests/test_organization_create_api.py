"""Tests for the Vault organization creation API."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.models import Base
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole


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
    """Open a database session for arranging and inspecting API effects."""
    with session_factory() as test_session:
        yield test_session


def create_api_user(db_session: Session, *, is_active: bool = True) -> User:
    """Create a default user for organization route tests."""
    user = create_user(
        db_session,
        email="owner@example.com",
        raw_password="safe password",
        full_name="Owner Example",
    )
    user.is_active = is_active
    db_session.commit()
    db_session.refresh(user)
    return user


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def organization_payload(name: str = "Example Company") -> dict[str, str]:
    """Build a valid organization creation payload."""
    return {"name": name}


def test_create_organization_without_token_returns_unauthorized(
    client: TestClient,
) -> None:
    response = client.post("/organizations", json=organization_payload())

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_create_organization_with_invalid_token_returns_unauthorized(
    client: TestClient,
) -> None:
    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers("not-a-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_create_organization_with_expired_token_returns_unauthorized(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    current_time = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_access_token(
        user.id,
        expires_delta=timedelta(minutes=-1),
        now=current_time,
    )

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_create_organization_with_valid_token_returns_created(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201


def test_create_organization_success_returns_organization_id(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["id"]


def test_create_organization_success_returns_trimmed_name(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload("  Example Company  "),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Example Company"


def test_create_organization_success_returns_creator_user_id(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["created_by_user_id"] == str(user.id)


def test_create_organization_success_returns_owner_role(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert response.json()["role"] == MembershipRole.OWNER.value


def test_create_organization_success_stores_organization(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    organization = db_session.scalar(select(Organization))
    assert organization is not None
    assert str(organization.id) == response.json()["id"]
    assert organization.name == "Example Company"


def test_create_organization_success_stores_owner_membership(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    membership = db_session.scalar(select(Membership))
    assert membership is not None
    assert str(membership.id) == response.json()["membership_id"]
    assert membership.user_id == user.id


def test_created_owner_membership_uses_official_owner_role(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    membership = db_session.scalar(select(Membership))
    assert membership is not None
    assert membership.role == MembershipRole.OWNER.value


def test_create_organization_rejects_blank_name(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(""),
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_organization_rejects_whitespace_only_name(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload("   "),
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_organization_rejects_inactive_user_token(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session, is_active=False)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_create_organization_response_does_not_include_password(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert "password" not in response.json()


def test_create_organization_response_does_not_include_password_hash(
    client: TestClient,
    db_session: Session,
) -> None:
    user = create_api_user(db_session)
    token = create_access_token(user.id)

    response = client.post(
        "/organizations",
        json=organization_payload(),
        headers=auth_headers(token),
    )

    assert response.status_code == 201
    assert "password_hash" not in response.json()


def test_openapi_schema_includes_organizations_path(
    client: TestClient,
) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/organizations" in response.json()["paths"]
