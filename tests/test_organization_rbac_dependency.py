"""Tests for organization RBAC route dependencies."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session, require_organization_roles
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for RBAC route tests."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db_session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Open a database session for arranging and inspecting API effects."""
    with session_factory() as test_session:
        yield test_session


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    """Create a test app with RBAC probe routes and database override."""
    app = create_app()
    _include_rbac_probe_routes(app)

    def override_database_session() -> Iterator[Session]:
        with session_factory() as test_session:
            yield test_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def _include_rbac_probe_routes(app: FastAPI) -> None:
    router = APIRouter(prefix="/rbac-probe")

    @router.get("/{organization_id}/owner")
    def owner_route(
        membership: Annotated[
            Membership,
            Depends(require_organization_roles(MembershipRole.OWNER)),
        ],
    ) -> dict[str, str]:
        return _membership_response(membership)

    @router.get("/{organization_id}/reviewer")
    def reviewer_route(
        membership: Annotated[
            Membership,
            Depends(require_organization_roles(MembershipRole.REVIEWER)),
        ],
    ) -> dict[str, str]:
        return _membership_response(membership)

    @router.get("/{organization_id}/viewer")
    def viewer_route(
        membership: Annotated[
            Membership,
            Depends(require_organization_roles(MembershipRole.VIEWER)),
        ],
    ) -> dict[str, str]:
        return _membership_response(membership)

    @router.get("/{organization_id}/owner-or-reviewer")
    def owner_or_reviewer_route(
        membership: Annotated[
            Membership,
            Depends(
                require_organization_roles(
                    MembershipRole.OWNER,
                    MembershipRole.REVIEWER,
                )
            ),
        ],
    ) -> dict[str, str]:
        return _membership_response(membership)

    app.include_router(router)


def _membership_response(membership: Membership) -> dict[str, str]:
    return {
        "membership_id": str(membership.id),
        "role": membership.role,
        "organization_id": str(membership.organization_id),
    }


def create_api_user(
    session: Session,
    *,
    email: str,
    full_name: str,
    is_active: bool = True,
) -> User:
    """Create a test user for organization RBAC tests."""
    user = create_user(
        session,
        email=email,
        raw_password="safe password",
        full_name=full_name,
    )
    user.is_active = is_active
    session.flush()
    return user


def add_membership(
    session: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MembershipRole,
) -> Membership:
    """Add an organization membership with an official role."""
    membership = Membership()
    membership.organization_id = organization_id
    membership.user_id = user_id
    membership.role = role.value
    session.add(membership)
    session.flush()
    return membership


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def organization_setup(db_session: Session) -> dict[str, object]:
    """Create users, an organization, and role memberships."""
    owner = create_api_user(
        db_session,
        email="owner-rbac@example.com",
        full_name="Owner RBAC",
    )
    reviewer = create_api_user(
        db_session,
        email="reviewer-rbac@example.com",
        full_name="Reviewer RBAC",
    )
    viewer = create_api_user(
        db_session,
        email="viewer-rbac@example.com",
        full_name="Viewer RBAC",
    )
    outsider = create_api_user(
        db_session,
        email="outsider-rbac@example.com",
        full_name="Outsider RBAC",
    )
    inactive_user = create_api_user(
        db_session,
        email="inactive-rbac@example.com",
        full_name="Inactive RBAC",
        is_active=False,
    )
    result = create_organization(
        db_session,
        creator=owner,
        name="RBAC Company",
    )
    reviewer_membership = add_membership(
        db_session,
        organization_id=result.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )
    viewer_membership = add_membership(
        db_session,
        organization_id=result.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )
    db_session.commit()
    return {
        "organization_id": result.organization.id,
        "owner": owner,
        "reviewer": reviewer,
        "viewer": viewer,
        "outsider": outsider,
        "inactive_user": inactive_user,
        "owner_membership": result.membership,
        "reviewer_membership": reviewer_membership,
        "viewer_membership": viewer_membership,
    }


def token_for(setup: dict[str, object], key: str) -> str:
    user = setup[key]
    assert isinstance(user, User)
    return create_access_token(user.id)


def organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def test_allowed_owner_role_is_permitted(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token_for(organization_setup, "owner")),
    )

    assert response.status_code == 200
    assert response.json()["role"] == MembershipRole.OWNER.value


def test_allowed_reviewer_role_is_permitted(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/reviewer",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 200
    assert response.json()["role"] == MembershipRole.REVIEWER.value


def test_allowed_viewer_role_is_permitted(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/viewer",
        headers=auth_headers(token_for(organization_setup, "viewer")),
    )

    assert response.status_code == 200
    assert response.json()["role"] == MembershipRole.VIEWER.value


def test_non_member_is_rejected_with_forbidden(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token_for(organization_setup, "outsider")),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_unknown_organization_is_rejected_with_forbidden(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    response = client.get(
        f"/rbac-probe/{uuid.uuid4()}/owner",
        headers=auth_headers(token_for(organization_setup, "owner")),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_member_with_wrong_role_is_rejected_with_forbidden(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_owner_is_not_allowed_when_only_reviewer_is_allowed(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/reviewer",
        headers=auth_headers(token_for(organization_setup, "owner")),
    )

    assert response.status_code == 403


def test_reviewer_is_not_allowed_when_only_owner_is_allowed(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 403


def test_viewer_is_not_allowed_when_owner_or_reviewer_is_required(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner-or-reviewer",
        headers=auth_headers(token_for(organization_setup, "viewer")),
    )

    assert response.status_code == 403


def test_multiple_allowed_roles_work_for_owner(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner-or-reviewer",
        headers=auth_headers(token_for(organization_setup, "owner")),
    )

    assert response.status_code == 200
    assert response.json()["role"] == MembershipRole.OWNER.value


def test_multiple_allowed_roles_work_for_reviewer(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner-or-reviewer",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 200
    assert response.json()["role"] == MembershipRole.REVIEWER.value


def test_missing_token_still_returns_unauthorized(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(f"/rbac-probe/{organization_id}/owner")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_still_returns_unauthorized(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers("not-a-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_still_returns_unauthorized(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)
    owner = organization_setup["owner"]
    assert isinstance(owner, User)
    current_time = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=current_time,
    )

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_still_returns_unauthorized(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/rbac-probe/{organization_id}/owner",
        headers=auth_headers(token_for(organization_setup, "inactive_user")),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_dependency_returns_matching_membership_when_access_is_allowed(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)
    expected_membership = organization_setup["reviewer_membership"]
    assert isinstance(expected_membership, Membership)

    response = client.get(
        f"/rbac-probe/{organization_id}/reviewer",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 200
    assert response.json()["membership_id"] == str(expected_membership.id)
    assert response.json()["organization_id"] == str(organization_id)


def test_get_organization_returns_ok_for_member(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/organizations/{organization_id}",
        headers=auth_headers(token_for(organization_setup, "viewer")),
    )

    assert response.status_code == 200


def test_get_organization_returns_safe_organization_data(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/organizations/{organization_id}",
        headers=auth_headers(token_for(organization_setup, "reviewer")),
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(organization_id)
    assert response.json()["name"] == "RBAC Company"
    assert "created_by_user_id" in response.json()
    assert "created_at" in response.json()
    assert "password" not in response.text
    assert "password_hash" not in response.text
    assert "membership_id" not in response.json()


def test_get_organization_rejects_non_members(
    client: TestClient,
    organization_setup: dict[str, object],
) -> None:
    organization_id = organization_id_from(organization_setup)

    response = client.get(
        f"/organizations/{organization_id}",
        headers=auth_headers(token_for(organization_setup, "outsider")),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_get_organization_appears_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/organizations/{organization_id}" in response.json()["paths"]
