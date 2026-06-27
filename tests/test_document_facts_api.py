"""Tests for Vault document facts API routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from typing import cast

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
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.documents.models import Document, DocumentFact
from vault.documents.service import create_document_fact, create_document_metadata
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64
SECOND_SHA256_HASH = "b" * 64
OTHER_SHA256_HASH = "c" * 64
SAFE_FACT_KEYS = {
    "id",
    "document_id",
    "vendor_name",
    "invoice_number",
    "invoice_date",
    "due_date",
    "amount_cents",
    "currency",
    "category",
    "memo",
    "created_at",
}


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for fact route tests."""
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
    """Create a test user for document facts API tests."""
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


def create_api_document(
    session: Session,
    *,
    organization_id: uuid.UUID,
    uploaded_by_user_id: uuid.UUID,
    original_filename: str,
    stored_filename: str,
    sha256_hash: str,
) -> Document:
    """Create document metadata for document fact API tests."""
    return create_document_metadata(
        session,
        organization_id=organization_id,
        uploaded_by_user_id=uploaded_by_user_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type="application/pdf",
        file_size_bytes=1024,
        sha256_hash=sha256_hash,
    )


@pytest.fixture
def fact_setup(db_session: Session) -> dict[str, object]:
    """Create users, organizations, documents, and starter facts."""
    owner = create_api_user(
        db_session,
        email="fact-owner@example.com",
        full_name="Fact Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="fact-reviewer@example.com",
        full_name="Fact Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="fact-viewer@example.com",
        full_name="Fact Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="fact-outsider@example.com",
        full_name="Fact Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="fact-inactive@example.com",
        full_name="Fact Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Fact Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Fact Company",
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
    document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="invoice.pdf",
        stored_filename="generated-invoice.pdf",
        sha256_hash=VALID_SHA256_HASH,
    )
    second_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="second.pdf",
        stored_filename="generated-second.pdf",
        sha256_hash=SECOND_SHA256_HASH,
    )
    other_document = create_api_document(
        db_session,
        organization_id=other_created.organization.id,
        uploaded_by_user_id=outsider.id,
        original_filename="other.pdf",
        stored_filename="generated-other.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    first_fact = create_document_fact(
        db_session,
        document_id=document.id,
        vendor_name="First Vendor",
        invoice_number="INV-1",
        invoice_date=date(2026, 1, 1),
        due_date=date(2026, 2, 1),
        amount_cents=1000,
        currency="USD",
        category="Meals",
        memo="First memo",
    )
    second_fact = create_document_fact(
        db_session,
        document_id=document.id,
        vendor_name="Second Vendor",
        amount_cents=2000,
        currency="USD",
        category="Supplies",
    )
    other_document_fact = create_document_fact(
        db_session,
        document_id=second_document.id,
        vendor_name="Other Document Vendor",
        amount_cents=3000,
        currency="USD",
        category="Software",
    )
    other_org_fact = create_document_fact(
        db_session,
        document_id=other_document.id,
        vendor_name="Other Org Vendor",
        amount_cents=4000,
        currency="USD",
        category="Travel",
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
        "document": document,
        "second_document": second_document,
        "other_document": other_document,
        "first_fact": first_fact,
        "second_fact": second_fact,
        "other_document_fact": other_document_fact,
        "other_org_fact": other_org_fact,
    }


def token_for(setup: dict[str, object], key: str) -> str:
    user = setup[key]
    assert isinstance(user, User)
    return create_access_token(user.id)


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def document_id_from(
    setup: dict[str, object],
    key: str = "document",
) -> uuid.UUID:
    document = setup[key]
    assert isinstance(document, Document)
    return document.id


def fact_id_from(
    setup: dict[str, object],
    key: str = "first_fact",
) -> uuid.UUID:
    fact = setup[key]
    assert isinstance(fact, DocumentFact)
    return fact.id


def facts_url(organization_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return f"/organizations/{organization_id}/documents/{document_id}/facts"


def fact_detail_url(
    organization_id: uuid.UUID,
    document_id: uuid.UUID,
    fact_id: uuid.UUID,
) -> str:
    return f"{facts_url(organization_id, document_id)}/{fact_id}"


def valid_fact_payload() -> dict[str, object]:
    return {
        "vendor_name": "  Example Vendor LLC  ",
        "invoice_number": "  INV-100  ",
        "invoice_date": "2026-01-15",
        "due_date": "2026-02-15",
        "amount_cents": 12345,
        "currency": " usd ",
        "category": "  Office Supplies  ",
        "memo": "  Monthly supplies  ",
    }


def create_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    payload: dict[str, object] | None = None,
    document_key: str = "document",
) -> Response:
    response = client.post(
        facts_url(organization_id_from(setup), document_id_from(setup, document_key)),
        headers=auth_headers(token_for(setup, user_key)),
        json=valid_fact_payload() if payload is None else payload,
    )
    return cast(Response, response)


def list_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    document_key: str = "document",
) -> Response:
    response = client.get(
        facts_url(organization_id_from(setup), document_id_from(setup, document_key)),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return cast(Response, response)


def detail_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    fact_key: str = "first_fact",
    document_key: str = "document",
) -> Response:
    response = client.get(
        fact_detail_url(
            organization_id_from(setup),
            document_id_from(setup, document_key),
            fact_id_from(setup, fact_key),
        ),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return cast(Response, response)


def assert_safe_fact_payload(payload: dict[str, object]) -> None:
    assert set(payload) == SAFE_FACT_KEYS
    assert "stored_path" not in payload
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "access_token" not in payload


def test_owner_can_create_fact(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "owner")

    assert response.status_code == 201


def test_reviewer_can_create_fact(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "reviewer")

    assert response.status_code == 201


def test_viewer_cannot_create_fact(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "viewer")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_non_member_cannot_create_fact(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_token_returns_unauthorized_for_create(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = client.post(
        facts_url(organization_id_from(fact_setup), document_id_from(fact_setup)),
        json=valid_fact_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized_for_create(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = client.post(
        facts_url(organization_id_from(fact_setup), document_id_from(fact_setup)),
        headers=auth_headers("not-a-valid-token"),
        json=valid_fact_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized_for_create(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    owner = fact_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    response = client.post(
        facts_url(organization_id_from(fact_setup), document_id_from(fact_setup)),
        headers=auth_headers(token),
        json=valid_fact_payload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_returns_unauthorized_for_create(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "inactive_user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_create_route_returns_safe_fact_metadata(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "owner")
    payload = response.json()

    assert response.status_code == 201
    assert_safe_fact_payload(payload)
    assert payload["document_id"] == str(document_id_from(fact_setup))


def test_create_route_persists_fact_row(
    client: TestClient,
    db_session: Session,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "owner")
    fact_id = uuid.UUID(response.json()["id"])

    fact = db_session.get(DocumentFact, fact_id)

    assert fact is not None


def test_create_route_stores_fact_fields(
    client: TestClient,
    db_session: Session,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "owner")
    fact_id = uuid.UUID(response.json()["id"])
    fact = db_session.get(DocumentFact, fact_id)

    assert fact is not None
    assert fact.document_id == document_id_from(fact_setup)
    assert fact.vendor_name == "Example Vendor LLC"
    assert fact.invoice_number == "INV-100"
    assert fact.invoice_date == date(2026, 1, 15)
    assert fact.due_date == date(2026, 2, 15)
    assert fact.amount_cents == 12345
    assert fact.currency == "USD"
    assert fact.category == "Office Supplies"
    assert fact.memo == "Monthly supplies"


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("vendor_name", "   "),
        ("currency", "   "),
        ("currency", "US1"),
        ("category", "   "),
        ("amount_cents", 0),
        ("amount_cents", -1),
    ],
)
def test_create_route_rejects_invalid_fact_values(
    client: TestClient,
    fact_setup: dict[str, object],
    field_name: str,
    field_value: object,
) -> None:
    payload = valid_fact_payload()
    payload[field_name] = field_value

    response = create_as(client, fact_setup, "owner", payload=payload)

    assert response.status_code == 400


def test_create_route_allows_optional_fields_to_be_omitted(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(
        client,
        fact_setup,
        "owner",
        payload={
            "vendor_name": "No Optional Vendor",
            "amount_cents": 500,
            "currency": "USD",
            "category": "Utilities",
        },
    )

    assert response.status_code == 201
    assert response.json()["invoice_number"] is None
    assert response.json()["invoice_date"] is None
    assert response.json()["due_date"] is None
    assert response.json()["memo"] is None


def test_duplicate_facts_are_allowed_for_now(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    first_response = create_as(client, fact_setup, "owner")
    second_response = create_as(client, fact_setup, "owner")

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_response.json()["id"] != second_response.json()["id"]


def test_cannot_create_fact_for_document_from_another_organization(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = create_as(client, fact_setup, "owner", document_key="other_document")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


@pytest.mark.parametrize("user_key", ["owner", "reviewer", "viewer"])
def test_allowed_members_can_list_facts(
    client: TestClient,
    fact_setup: dict[str, object],
    user_key: str,
) -> None:
    response = list_as(client, fact_setup, user_key)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_member_cannot_list_facts(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = list_as(client, fact_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_list_route_returns_only_facts_for_requested_document(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = list_as(client, fact_setup, "owner")

    returned_ids = {item["id"] for item in response.json()}
    assert str(fact_id_from(fact_setup, "first_fact")) in returned_ids
    assert str(fact_id_from(fact_setup, "second_fact")) in returned_ids


def test_list_route_does_not_leak_facts_from_another_document(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = list_as(client, fact_setup, "owner")

    returned_ids = {item["id"] for item in response.json()}
    assert str(fact_id_from(fact_setup, "other_document_fact")) not in returned_ids


def test_list_route_does_not_leak_facts_through_cross_org_document(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = list_as(client, fact_setup, "owner", document_key="other_document")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_list_route_returns_safe_metadata(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = list_as(client, fact_setup, "owner")

    for item in response.json():
        assert_safe_fact_payload(item)


@pytest.mark.parametrize("user_key", ["owner", "reviewer", "viewer"])
def test_allowed_members_can_read_fact_detail(
    client: TestClient,
    fact_setup: dict[str, object],
    user_key: str,
) -> None:
    response = detail_as(client, fact_setup, user_key)

    assert response.status_code == 200
    assert response.json()["id"] == str(fact_id_from(fact_setup))


def test_non_member_cannot_read_fact_detail(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(client, fact_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_fact_detail_returns_not_found(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = client.get(
        fact_detail_url(
            organization_id_from(fact_setup),
            document_id_from(fact_setup),
            uuid.uuid4(),
        ),
        headers=auth_headers(token_for(fact_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document fact was not found."


def test_fact_detail_scopes_by_document_id_and_fact_id(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(
        client,
        fact_setup,
        "owner",
        fact_key="other_document_fact",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document fact was not found."


def test_fact_from_another_document_is_not_returned(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(
        client,
        fact_setup,
        "owner",
        fact_key="other_org_fact",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document fact was not found."


def test_all_new_fact_routes_appear_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert (
        "/organizations/{organization_id}/documents/{document_id}/facts"
        in paths
    )
    assert (
        "/organizations/{organization_id}/documents/{document_id}/facts/{fact_id}"
        in paths
    )


def test_fact_responses_do_not_include_local_absolute_paths(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(client, fact_setup, "owner")

    assert "stored_path" not in response.text
    assert "/tmp/" not in response.text
    assert "C:\\" not in response.text


def test_fact_responses_do_not_include_raw_passwords(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(client, fact_setup, "owner")

    assert "safe password" not in response.text
    assert "password" not in response.text


def test_fact_responses_do_not_include_password_hashes(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = detail_as(client, fact_setup, "owner")

    assert "password_hash" not in response.text
    assert "$argon2" not in response.text


def test_missing_document_in_accessible_org_returns_safe_not_found(
    client: TestClient,
    fact_setup: dict[str, object],
) -> None:
    response = client.get(
        facts_url(organization_id_from(fact_setup), uuid.uuid4()),
        headers=auth_headers(token_for(fact_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_fact_creation_creates_document_fact_audit_entry(
    client: TestClient,
    fact_setup: dict[str, object],
    db_session: Session,
) -> None:
    owner = fact_setup["owner"]
    assert isinstance(owner, User)

    response = create_as(client, fact_setup, "owner")

    assert response.status_code == 201
    audit_entries = db_session.scalars(select(AuditEntry)).all()
    audit_entry = audit_entries[-1]
    assert audit_entry.action == AuditAction.DOCUMENT_FACT_CREATED.value
    assert audit_entry.entity_type == AuditEntityType.DOCUMENT_FACT.value
    assert str(audit_entry.entity_id) == response.json()["id"]
    assert str(audit_entry.organization_id) == str(organization_id_from(fact_setup))
    assert audit_entry.actor_user_id == owner.id
    assert audit_entry.metadata_json["vendor_name"] == "Example Vendor LLC"
    assert audit_entry.metadata_json["invoice_number"] == "INV-100"
    assert audit_entry.metadata_json["amount_cents"] == 12345
    assert audit_entry.metadata_json["currency"] == "USD"
    assert audit_entry.metadata_json["category"] == "Office Supplies"


def test_fact_creation_validation_failure_does_not_create_audit_entry(
    client: TestClient,
    fact_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = create_as(
        client,
        fact_setup,
        "owner",
        payload={**valid_fact_payload(), "amount_cents": 0},
    )

    assert response.status_code == 400
    assert db_session.scalars(select(AuditEntry)).all() == []


def test_viewer_denied_fact_creation_does_not_create_audit_entry(
    client: TestClient,
    fact_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = create_as(client, fact_setup, "viewer")

    assert response.status_code == 403
    assert db_session.scalars(select(AuditEntry)).all() == []
