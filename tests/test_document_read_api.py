"""Tests for Vault document listing and detail APIs."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.documents.models import Document
from vault.documents.service import create_document_metadata
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

FIRST_HASH = "1" * 64
SECOND_HASH = "2" * 64
OTHER_HASH = "3" * 64
SAFE_DOCUMENT_KEYS = {
    "id",
    "organization_id",
    "uploaded_by_user_id",
    "original_filename",
    "stored_filename",
    "content_type",
    "file_size_bytes",
    "sha256_hash",
    "status",
    "created_at",
}


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for document read tests."""
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
    """Create a test client with a dependency-overridden database session."""
    app = create_app()

    def override_database_session() -> Iterator[Session]:
        with session_factory() as test_session:
            yield test_session

    app.dependency_overrides[get_database_session] = override_database_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def create_api_user(
    session: Session,
    *,
    email: str,
    full_name: str,
    is_active: bool = True,
) -> User:
    """Create a test user for document read API tests."""
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


def create_read_document(
    session: Session,
    *,
    organization_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID,
    original_filename: str,
    stored_filename: str,
    sha256_hash: str,
    created_at: datetime,
) -> Document:
    """Create document metadata for document read API tests."""
    document = create_document_metadata(
        session,
        organization_id=organization_id,
        uploaded_by_user_id=uploaded_by_user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=sha256_hash,
    )
    document.created_at = created_at
    session.flush()
    return document


@pytest.fixture
def read_setup(db_session: Session) -> dict[str, object]:
    """Create users, organizations, memberships, and documents."""
    owner = create_api_user(
        db_session,
        email="read-owner@example.com",
        full_name="Read Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="read-reviewer@example.com",
        full_name="Read Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="read-viewer@example.com",
        full_name="Read Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="read-outsider@example.com",
        full_name="Read Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="read-inactive@example.com",
        full_name="Read Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Read Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Read Company",
    )
    add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )
    add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )
    older_document = create_read_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="older.pdf",
        stored_filename="generated-older.pdf",
        sha256_hash=FIRST_HASH,
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    newer_document = create_read_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=reviewer.id,
        original_filename="newer.pdf",
        stored_filename="generated-newer.pdf",
        sha256_hash=SECOND_HASH,
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
    )
    other_document = create_read_document(
        db_session,
        organization_id=other_created.organization.id,
        uploaded_by_user_id=outsider.id,
        original_filename="other.pdf",
        stored_filename="generated-other.pdf",
        sha256_hash=OTHER_HASH,
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    db_session.commit()
    return {
        "organization_id": created.organization.id,
        "other_organization_id": other_created.organization.id,
        "owner": owner,
        "reviewer": reviewer,
        "viewer": viewer,
        "outsider": outsider,
        "inactive_user": inactive_user,
        "older_document": older_document,
        "newer_document": newer_document,
        "other_document": other_document,
    }


def token_for(setup: dict[str, object], key: str) -> str:
    user = setup[key]
    assert isinstance(user, User)
    return create_access_token(user.id)


def organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def document_id_from(
    setup: dict[str, object],
    key: str = "newer_document",
) -> uuid.UUID:
    document = setup[key]
    assert isinstance(document, Document)
    return document.id


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def list_url(organization_id: uuid.UUID) -> str:
    return f"/organizations/{organization_id}/documents"


def detail_url(organization_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return f"/organizations/{organization_id}/documents/{document_id}"


def list_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
) -> Response:
    response: Response = client.get(
        list_url(organization_id_from(setup)),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def detail_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    document_key: str = "newer_document",
) -> Response:
    response: Response = client.get(
        detail_url(
            organization_id_from(setup),
            document_id_from(setup, document_key),
        ),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def assert_safe_document_payload(payload: dict[str, object]) -> None:
    assert set(payload) == SAFE_DOCUMENT_KEYS
    assert "stored_path" not in payload
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "/" not in str(payload["stored_filename"])
    assert "\\" not in str(payload["stored_filename"])


def test_owner_can_list_documents(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_reviewer_can_list_documents(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "reviewer")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_viewer_can_list_documents(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "viewer")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_member_cannot_list_documents(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_token_returns_unauthorized_for_list_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = client.get(list_url(organization_id_from(read_setup)))

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized_for_list_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        list_url(organization_id_from(read_setup)),
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized_for_list_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    owner = read_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    response: Response = client.get(
        list_url(organization_id_from(read_setup)),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_returns_unauthorized_for_list_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "inactive_user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_list_route_returns_only_documents_for_requested_organization(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    returned_ids = {item["id"] for item in response.json()}
    assert str(document_id_from(read_setup, "older_document")) in returned_ids
    assert str(document_id_from(read_setup, "newer_document")) in returned_ids


def test_list_route_does_not_leak_documents_from_another_organization(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    returned_ids = {item["id"] for item in response.json()}
    assert str(document_id_from(read_setup, "other_document")) not in returned_ids


def test_list_route_returns_newest_documents_first(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    returned_ids = [item["id"] for item in response.json()]
    assert returned_ids == [
        str(document_id_from(read_setup, "newer_document")),
        str(document_id_from(read_setup, "older_document")),
    ]


def test_list_route_returns_safe_metadata(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    for item in response.json():
        assert_safe_document_payload(item)


def test_list_route_does_not_include_local_absolute_paths(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    body = response.text
    assert "stored_path" not in body
    assert "/tmp/" not in body
    assert "C:\\" not in body


def test_list_route_does_not_include_raw_passwords(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    assert "safe password" not in response.text
    assert "password" not in response.text


def test_list_route_does_not_include_password_hashes(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = list_as(client, read_setup, "owner")

    assert "password_hash" not in response.text
    assert "$argon2" not in response.text


def test_list_route_appears_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert "/organizations/{organization_id}/documents" in response.json()["paths"]


def test_owner_can_read_document_detail(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "owner")

    assert response.status_code == 200
    assert response.json()["id"] == str(document_id_from(read_setup))


def test_reviewer_can_read_document_detail(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "reviewer")

    assert response.status_code == 200
    assert response.json()["id"] == str(document_id_from(read_setup))


def test_viewer_can_read_document_detail(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "viewer")

    assert response.status_code == 200
    assert response.json()["id"] == str(document_id_from(read_setup))


def test_non_member_cannot_read_document_detail(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_token_returns_unauthorized_for_detail_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        detail_url(
            organization_id_from(read_setup),
            document_id_from(read_setup),
        )
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized_for_detail_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        detail_url(
            organization_id_from(read_setup),
            document_id_from(read_setup),
        ),
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized_for_detail_route(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    owner = read_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    response: Response = client.get(
        detail_url(
            organization_id_from(read_setup),
            document_id_from(read_setup),
        ),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_detail_route_returns_not_found_for_missing_document(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        detail_url(organization_id_from(read_setup), uuid.uuid4()),
        headers=auth_headers(token_for(read_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_detail_route_does_not_return_document_from_another_organization(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        detail_url(
            organization_id_from(read_setup),
            document_id_from(read_setup, "other_document"),
        ),
        headers=auth_headers(token_for(read_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_detail_route_returns_safe_metadata(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "owner")

    assert_safe_document_payload(response.json())


def test_detail_route_does_not_include_local_absolute_paths(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "owner")

    body = response.text
    assert "stored_path" not in body
    assert "/tmp/" not in body
    assert "C:\\" not in body


def test_detail_route_does_not_include_raw_passwords(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "owner")

    assert "safe password" not in response.text
    assert "password" not in response.text


def test_detail_route_does_not_include_password_hashes(
    client: TestClient,
    read_setup: dict[str, object],
) -> None:
    response = detail_as(client, read_setup, "owner")

    assert "password_hash" not in response.text
    assert "$argon2" not in response.text


def test_detail_route_appears_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    path = "/organizations/{organization_id}/documents/{document_id}"
    assert path in response.json()["paths"]
