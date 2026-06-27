"""Tests for Vault audit API routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.audit.service import create_audit_entry
from vault.auth.models import User
from vault.auth.tokens import create_access_token
from vault.models import Base
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

SAFE_AUDIT_KEYS = {
    "id",
    "organization_id",
    "actor_user_id",
    "action",
    "entity_type",
    "entity_id",
    "summary",
    "metadata_json",
    "created_at",
}
SENSITIVE_FRAGMENTS = (
    "raw-secret-password",
    "argon2id",
    "bearer super-secret-token",
    "token payload",
    "/home/nathan/vault/uploads/private.pdf",
    "C:\\Users\\Nathan\\vault\\uploads\\private.pdf",
)


@dataclass(frozen=True)
class AuditApiSetup:
    """Database records used by audit route tests."""

    owner: User
    reviewer: User
    viewer: User
    outsider: User
    inactive_user: User
    organization: Organization
    other_organization: Organization
    older_entry: AuditEntry
    newer_entry: AuditEntry
    other_org_entry: AuditEntry
    org_null_entry: AuditEntry


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for audit route tests."""
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
    """Create a test user for audit API tests."""
    user = User()
    user.email = email
    user.password_hash = "fake-test-password-hash"
    user.full_name = full_name
    user.is_active = is_active
    session.add(user)
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


def create_api_audit_entry(
    session: Session,
    *,
    organization_id: uuid.UUID | None,
    actor_user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    summary: str,
    created_at: datetime,
    metadata_json: dict[str, Any] | None = None,
) -> AuditEntry:
    """Create an audit entry with a fixed timestamp for API tests."""
    entry = create_audit_entry(
        session,
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_json={} if metadata_json is None else metadata_json,
    )
    entry.created_at = created_at
    session.flush()
    return entry


@pytest.fixture
def audit_setup(db_session: Session) -> AuditApiSetup:
    """Create users, organizations, memberships, and audit entries."""
    owner = create_api_user(
        db_session,
        email="audit-owner@example.com",
        full_name="Audit Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="audit-reviewer@example.com",
        full_name="Audit Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="audit-viewer@example.com",
        full_name="Audit Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="audit-outsider@example.com",
        full_name="Audit Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="audit-inactive@example.com",
        full_name="Audit Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Audit Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Audit Company",
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
    older_entry = create_api_audit_entry(
        db_session,
        organization_id=created.organization.id,
        actor_user_id=owner.id,
        action=AuditAction.DOCUMENT_UPLOADED.value,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=uuid.uuid4(),
        summary="Document uploaded.",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        metadata_json={"original_filename": "invoice.pdf"},
    )
    newer_entry = create_api_audit_entry(
        db_session,
        organization_id=created.organization.id,
        actor_user_id=reviewer.id,
        action=AuditAction.REVIEW_DECISION_CREATED.value,
        entity_type=AuditEntityType.REVIEW_DECISION.value,
        entity_id=uuid.uuid4(),
        summary="Review decision created.",
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        metadata_json=_unsafe_metadata_example(),
    )
    other_org_entry = create_api_audit_entry(
        db_session,
        organization_id=other_created.organization.id,
        actor_user_id=outsider.id,
        action=AuditAction.ORGANIZATION_CREATED.value,
        entity_type=AuditEntityType.ORGANIZATION.value,
        entity_id=other_created.organization.id,
        summary="Other organization created.",
        created_at=datetime(2026, 1, 3, tzinfo=UTC),
    )
    org_null_entry = create_api_audit_entry(
        db_session,
        organization_id=None,
        actor_user_id=owner.id,
        action=AuditAction.USER_REGISTERED.value,
        entity_type=AuditEntityType.USER.value,
        entity_id=owner.id,
        summary="User registered.",
        created_at=datetime(2026, 1, 4, tzinfo=UTC),
    )
    db_session.commit()
    return AuditApiSetup(
        owner=owner,
        reviewer=reviewer,
        viewer=viewer,
        outsider=outsider,
        inactive_user=inactive_user,
        organization=created.organization,
        other_organization=other_created.organization,
        older_entry=older_entry,
        newer_entry=newer_entry,
        other_org_entry=other_org_entry,
        org_null_entry=org_null_entry,
    )


def _unsafe_metadata_example() -> dict[str, Any]:
    return {
        "raw_password": "raw-secret-password",
        "password_hash": "$argon2id$v=19$hash-value",
        "authorization": "Bearer super-secret-token",
        "token_payload": {"sub": "token payload"},
        "stored_path": "/home/nathan/vault/uploads/private.pdf",
        "windows_path": "C:\\Users\\Nathan\\vault\\uploads\\private.pdf",
        "safe_nested": {"document_id": "safe-document-id"},
    }


def auth_headers(user: User, *, expired: bool = False) -> dict[str, str]:
    """Build bearer auth headers for a test user."""
    expires_delta = timedelta(minutes=-1 if expired else 30)
    token = create_access_token(user.id, expires_delta=expires_delta)
    return {"Authorization": f"Bearer {token}"}


def list_audit(
    client: TestClient,
    setup: AuditApiSetup,
    user: User,
    query: str = "",
) -> Response:
    """Request the audit list route as one user."""
    response: Response = client.get(
        f"/organizations/{setup.organization.id}/audit{query}",
        headers=auth_headers(user),
    )
    return response


def read_audit_detail(
    client: TestClient,
    setup: AuditApiSetup,
    user: User,
    audit_entry_id: uuid.UUID,
) -> Response:
    """Request the audit detail route as one user."""
    response: Response = client.get(
        f"/organizations/{setup.organization.id}/audit/{audit_entry_id}",
        headers=auth_headers(user),
    )
    return response


def response_items(response: Response) -> list[dict[str, Any]]:
    """Return a typed list response payload."""
    return cast(list[dict[str, Any]], response.json())


def response_object(response: Response) -> dict[str, Any]:
    """Return a typed object response payload."""
    return cast(dict[str, Any], response.json())


def all_text(value: object) -> str:
    """Flatten nested response content into lowercase text."""
    return str(value).lower()


def audit_entry_count(session: Session) -> int:
    """Count audit entries in the test database."""
    return len(list(session.scalars(select(AuditEntry))))


def test_owner_can_list_audit_entries(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)

    assert response.status_code == 200
    assert len(response_items(response)) == 2


def test_reviewer_can_list_audit_entries(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.reviewer)

    assert response.status_code == 200


def test_viewer_can_list_audit_entries(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.viewer)

    assert response.status_code == 200


def test_non_member_cannot_list_audit_entries(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.outsider)

    assert response.status_code == 403
    assert response.json() == {"detail": "Organization access is not available."}


def test_missing_token_returns_http_401_for_audit_listing(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = client.get(f"/organizations/{audit_setup.organization.id}/audit")

    assert response.status_code == 401


def test_invalid_token_returns_http_401_for_audit_listing(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response: Response = client.get(
        f"/organizations/{audit_setup.organization.id}/audit",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_expired_token_returns_http_401_for_audit_listing(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response: Response = client.get(
        f"/organizations/{audit_setup.organization.id}/audit",
        headers=auth_headers(audit_setup.owner, expired=True),
    )

    assert response.status_code == 401


def test_inactive_user_token_returns_http_401_for_audit_listing(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response: Response = client.get(
        f"/organizations/{audit_setup.organization.id}/audit",
        headers=auth_headers(audit_setup.inactive_user),
    )

    assert response.status_code == 401


def test_unknown_organization_returns_existing_safe_http_403_behavior(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response: Response = client.get(
        f"/organizations/{uuid.uuid4()}/audit",
        headers=auth_headers(audit_setup.owner),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Organization access is not available."}


def test_audit_list_returns_only_entries_for_requested_organization(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)
    ids = {item["id"] for item in response_items(response)}

    assert str(audit_setup.older_entry.id) in ids
    assert str(audit_setup.newer_entry.id) in ids


def test_audit_list_does_not_leak_entries_from_another_organization(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)
    ids = {item["id"] for item in response_items(response)}

    assert str(audit_setup.other_org_entry.id) not in ids


def test_audit_list_excludes_organization_null_entries(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)
    ids = {item["id"] for item in response_items(response)}

    assert str(audit_setup.org_null_entry.id) not in ids


def test_audit_list_returns_deterministic_newest_first_ordering(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)
    ids = [item["id"] for item in response_items(response)]

    assert ids == [str(audit_setup.newer_entry.id), str(audit_setup.older_entry.id)]


def test_audit_list_returns_safe_metadata(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)
    first_item = response_items(response)[0]

    assert set(first_item) == SAFE_AUDIT_KEYS
    assert first_item["metadata_json"]["safe_nested"] == {
        "document_id": "safe-document-id",
    }


@pytest.mark.parametrize("fragment", SENSITIVE_FRAGMENTS)
def test_audit_list_responses_do_not_include_sensitive_metadata(
    client: TestClient,
    audit_setup: AuditApiSetup,
    fragment: str,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner)

    assert fragment.lower() not in all_text(response.json())


def test_owner_can_read_audit_entry_detail(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.newer_entry.id,
    )

    assert response.status_code == 200
    assert response_object(response)["id"] == str(audit_setup.newer_entry.id)


def test_reviewer_can_read_audit_entry_detail(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.reviewer,
        audit_setup.newer_entry.id,
    )

    assert response.status_code == 200


def test_viewer_can_read_audit_entry_detail(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.viewer,
        audit_setup.newer_entry.id,
    )

    assert response.status_code == 200


def test_non_member_cannot_read_audit_entry_detail(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.outsider,
        audit_setup.newer_entry.id,
    )

    assert response.status_code == 403


def test_missing_audit_detail_returns_http_404(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        uuid.uuid4(),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Audit entry was not found."}


def test_audit_detail_scopes_by_organization_id_and_audit_entry_id(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.older_entry.id,
    )

    assert response.status_code == 200
    assert response_object(response)["organization_id"] == str(
        audit_setup.organization.id
    )


def test_audit_entry_from_another_organization_is_not_returned(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.other_org_entry.id,
    )

    assert response.status_code == 404


def test_organization_null_audit_entry_is_not_returned_through_detail_lookup(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.org_null_entry.id,
    )

    assert response.status_code == 404


def test_audit_detail_returns_safe_metadata(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.newer_entry.id,
    )
    payload = response_object(response)

    assert set(payload) == SAFE_AUDIT_KEYS
    assert payload["metadata_json"]["safe_nested"] == {
        "document_id": "safe-document-id",
    }


@pytest.mark.parametrize("fragment", SENSITIVE_FRAGMENTS)
def test_audit_detail_responses_do_not_include_sensitive_metadata(
    client: TestClient,
    audit_setup: AuditApiSetup,
    fragment: str,
) -> None:
    response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.newer_entry.id,
    )

    assert fragment.lower() not in all_text(response.json())


def test_audit_routes_appear_in_openapi(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    assert "/organizations/{organization_id}/audit" in schema["paths"]
    assert "/organizations/{organization_id}/audit/{audit_entry_id}" in schema["paths"]


def test_audit_read_routes_do_not_create_new_audit_entries(
    client: TestClient,
    db_session: Session,
    audit_setup: AuditApiSetup,
) -> None:
    before_count = audit_entry_count(db_session)

    list_response = list_audit(client, audit_setup, audit_setup.owner)
    detail_response = read_audit_detail(
        client,
        audit_setup,
        audit_setup.owner,
        audit_setup.newer_entry.id,
    )

    db_session.expire_all()
    assert list_response.status_code == 200
    assert detail_response.status_code == 200
    assert audit_entry_count(db_session) == before_count


def test_filtering_by_action_remains_organization_scoped(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(
        client,
        audit_setup,
        audit_setup.owner,
        query=f"?action={AuditAction.DOCUMENT_UPLOADED.value}",
    )
    ids = [item["id"] for item in response_items(response)]

    assert ids == [str(audit_setup.older_entry.id)]


def test_filtering_by_entity_type_remains_organization_scoped(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(
        client,
        audit_setup,
        audit_setup.owner,
        query=f"?entity_type={AuditEntityType.REVIEW_DECISION.value}",
    )
    ids = [item["id"] for item in response_items(response)]

    assert ids == [str(audit_setup.newer_entry.id)]


def test_filtering_by_entity_id_remains_organization_scoped(
    client: TestClient,
    audit_setup: AuditApiSetup,
) -> None:
    response = list_audit(
        client,
        audit_setup,
        audit_setup.owner,
        query=f"?entity_id={audit_setup.newer_entry.entity_id}",
    )
    ids = [item["id"] for item in response_items(response)]

    assert ids == [str(audit_setup.newer_entry.id)]


@pytest.mark.parametrize(
    "query",
    ["?action=unsupported_action", "?entity_type=unsupported_entity"],
)
def test_unsupported_filters_return_http_400_safely(
    client: TestClient,
    audit_setup: AuditApiSetup,
    query: str,
) -> None:
    response = list_audit(client, audit_setup, audit_setup.owner, query=query)

    assert response.status_code == 400
    assert "not supported" in response_object(response)["detail"]
