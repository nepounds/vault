"""Tests for Vault control flag API routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta

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
from vault.controls.models import ControlFlag
from vault.controls.service import create_control_flag
from vault.controls.severities import ControlFlagSeverity
from vault.controls.types import ControlFlagType
from vault.documents.models import Document
from vault.documents.service import create_document_fact, create_document_metadata
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64
SECOND_SHA256_HASH = "b" * 64
THIRD_SHA256_HASH = "c" * 64
FOURTH_SHA256_HASH = "d" * 64
FIFTH_SHA256_HASH = "e" * 64
OTHER_SHA256_HASH = "f" * 64
SAFE_FLAG_KEYS = {
    "id",
    "document_id",
    "flag_type",
    "severity",
    "reason",
    "created_at",
}


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for flag route tests."""
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
    """Create a test user for control flag API tests."""
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
    """Create document metadata for control flag API tests."""
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
def flag_setup(db_session: Session) -> dict[str, object]:
    """Create users, organizations, documents, facts, and starter flags."""
    owner = create_api_user(
        db_session,
        email="flag-owner@example.com",
        full_name="Flag Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="flag-reviewer@example.com",
        full_name="Flag Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="flag-viewer@example.com",
        full_name="Flag Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="flag-outsider@example.com",
        full_name="Flag Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="flag-inactive@example.com",
        full_name="Flag Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Flag Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Flag Company",
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
    clean_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="clean.pdf",
        stored_filename="generated-clean.pdf",
        sha256_hash=SECOND_SHA256_HASH,
    )
    no_fact_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="no-facts.pdf",
        stored_filename="generated-no-facts.pdf",
        sha256_hash=THIRD_SHA256_HASH,
    )
    flag_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="flagged.pdf",
        stored_filename="generated-flagged.pdf",
        sha256_hash=FOURTH_SHA256_HASH,
    )
    other_document = create_api_document(
        db_session,
        organization_id=other_created.organization.id,
        uploaded_by_user_id=outsider.id,
        original_filename="other.pdf",
        stored_filename="generated-other.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    second_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="second.pdf",
        stored_filename="generated-second.pdf",
        sha256_hash=FIFTH_SHA256_HASH,
    )
    create_document_fact(
        db_session,
        document_id=document.id,
        vendor_name="Needs Review Vendor",
        invoice_date=None,
        due_date=None,
        amount_cents=150_000,
        currency="cad",
        category="Supplies",
    )
    create_document_fact(
        db_session,
        document_id=clean_document.id,
        vendor_name="Clean Vendor",
        invoice_number="INV-100",
        invoice_date=date(2026, 1, 15),
        due_date=date(2026, 2, 15),
        amount_cents=999,
        currency="USD",
        category="Meals",
    )
    blocker_flag = create_control_flag(
        db_session,
        document_id=flag_document.id,
        flag_type=ControlFlagType.HIGH_AMOUNT.value,
        severity=ControlFlagSeverity.BLOCKER.value,
        reason="Invoice amount is high enough to require extra review.",
    )
    warning_flag = create_control_flag(
        db_session,
        document_id=flag_document.id,
        flag_type=ControlFlagType.MISSING_INVOICE_NUMBER.value,
        severity=ControlFlagSeverity.WARNING.value,
        reason="Invoice number is missing.",
    )
    info_flag = create_control_flag(
        db_session,
        document_id=flag_document.id,
        flag_type=ControlFlagType.MISSING_DUE_DATE.value,
        severity=ControlFlagSeverity.INFO.value,
        reason="Due date is missing.",
    )
    other_document_flag = create_control_flag(
        db_session,
        document_id=second_document.id,
        flag_type=ControlFlagType.MISSING_INVOICE_DATE.value,
        severity=ControlFlagSeverity.WARNING.value,
        reason="Invoice date is missing.",
    )
    other_org_flag = create_control_flag(
        db_session,
        document_id=other_document.id,
        flag_type=ControlFlagType.NON_USD_CURRENCY.value,
        severity=ControlFlagSeverity.WARNING.value,
        reason="Currency is not USD.",
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
        "clean_document": clean_document,
        "no_fact_document": no_fact_document,
        "flag_document": flag_document,
        "second_document": second_document,
        "other_document": other_document,
        "blocker_flag": blocker_flag,
        "warning_flag": warning_flag,
        "info_flag": info_flag,
        "other_document_flag": other_document_flag,
        "other_org_flag": other_org_flag,
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


def other_organization_id_from(setup: dict[str, object]) -> uuid.UUID:
    organization_id = setup["other_organization_id"]
    assert isinstance(organization_id, uuid.UUID)
    return organization_id


def document_id_from(
    setup: dict[str, object],
    key: str = "document",
) -> uuid.UUID:
    document = setup[key]
    assert isinstance(document, Document)
    return document.id


def flag_id_from(
    setup: dict[str, object],
    key: str = "blocker_flag",
) -> uuid.UUID:
    flag = setup[key]
    assert isinstance(flag, ControlFlag)
    return flag.id


def flags_url(organization_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return f"/organizations/{organization_id}/documents/{document_id}/control-flags"


def generate_url(organization_id: uuid.UUID, document_id: uuid.UUID) -> str:
    return f"{flags_url(organization_id, document_id)}/generate"


def flag_detail_url(
    organization_id: uuid.UUID,
    document_id: uuid.UUID,
    flag_id: uuid.UUID,
) -> str:
    return f"{flags_url(organization_id, document_id)}/{flag_id}"


def generate_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    document_key: str = "document",
) -> Response:
    response: Response = client.post(
        generate_url(
            organization_id_from(setup),
            document_id_from(setup, document_key),
        ),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def list_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    document_key: str = "flag_document",
) -> Response:
    response: Response = client.get(
        flags_url(organization_id_from(setup), document_id_from(setup, document_key)),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def detail_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    flag_key: str = "blocker_flag",
    document_key: str = "flag_document",
) -> Response:
    response: Response = client.get(
        flag_detail_url(
            organization_id_from(setup),
            document_id_from(setup, document_key),
            flag_id_from(setup, flag_key),
        ),
        headers=auth_headers(token_for(setup, user_key)),
    )
    return response


def assert_safe_flag_payload(payload: dict[str, object]) -> None:
    assert set(payload) == SAFE_FLAG_KEYS
    assert "stored_path" not in payload
    assert "stored_filename" not in payload
    assert "password" not in payload
    assert "password_hash" not in payload
    assert "access_token" not in payload


def generated_flag_rows(
    session: Session,
    *,
    document_id: uuid.UUID,
) -> list[ControlFlag]:
    statement = select(ControlFlag).where(ControlFlag.document_id == document_id)
    return list(session.scalars(statement))


def test_owner_can_generate_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner")

    assert response.status_code == 200
    assert response.json()


def test_reviewer_can_generate_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "reviewer")

    assert response.status_code == 200
    assert response.json()


def test_viewer_cannot_generate_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "viewer")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_non_member_cannot_generate_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_token_returns_unauthorized_for_generate(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(organization_id_from(flag_setup), document_id_from(flag_setup)),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized_for_generate(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(organization_id_from(flag_setup), document_id_from(flag_setup)),
        headers=auth_headers("not-a-valid-token"),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized_for_generate(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    owner = flag_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )
    response: Response = client.post(
        generate_url(organization_id_from(flag_setup), document_id_from(flag_setup)),
        headers=auth_headers(token),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_returns_unauthorized_for_generate(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "inactive_user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_generation_verifies_document_belongs_to_path_organization(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            other_organization_id_from(flag_setup),
            document_id_from(flag_setup, "document"),
        ),
        headers=auth_headers(token_for(flag_setup, "outsider")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_generation_rejects_document_from_another_organization(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.post(
        generate_url(
            organization_id_from(flag_setup),
            document_id_from(flag_setup, "other_document"),
        ),
        headers=auth_headers(token_for(flag_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_generation_returns_safe_control_flag_metadata(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner")
    payload = response.json()[0]

    assert response.status_code == 200
    assert_safe_flag_payload(payload)
    assert payload["document_id"] == str(document_id_from(flag_setup))


def test_generation_persists_control_flag_rows(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)
    rows = generated_flag_rows(db_session, document_id=document_id)

    assert response.status_code == 200
    assert rows


def test_generated_rows_store_document_id(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)

    assert all(flag.document_id == document_id for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    ))


def test_generated_rows_store_flag_type(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)
    flag_types = {flag.flag_type for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    )}

    assert ControlFlagType.MISSING_INVOICE_NUMBER.value in flag_types
    assert ControlFlagType.HIGH_AMOUNT.value in flag_types


def test_generated_rows_store_severity(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)
    severities = {flag.severity for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    )}

    assert ControlFlagSeverity.WARNING.value in severities
    assert ControlFlagSeverity.BLOCKER.value in severities


def test_generated_rows_store_reason(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)
    reasons = [flag.reason for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    )]

    assert all(reasons)
    assert "Invoice amount is high enough to require extra review." in reasons


def test_generated_rows_have_ids(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)

    assert all(flag.id for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    ))


def test_generated_rows_have_created_timestamps(
    client: TestClient,
    db_session: Session,
    flag_setup: dict[str, object],
) -> None:
    generate_as(client, flag_setup, "owner")
    document_id = document_id_from(flag_setup)

    assert all(flag.created_at for flag in generated_flag_rows(
        db_session,
        document_id=document_id,
    ))


def test_generation_returns_empty_list_when_no_flags_are_generated(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner", "clean_document")

    assert response.status_code == 200
    assert response.json() == []


def test_generation_returns_empty_list_when_document_has_no_facts(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner", "no_fact_document")

    assert response.status_code == 200
    assert response.json() == []


def test_generation_does_not_create_duplicate_file_hash_flags_yet(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner")
    flag_types = {payload["flag_type"] for payload in response.json()}

    assert ControlFlagType.DUPLICATE_FILE_HASH.value not in flag_types


def test_generation_does_not_create_duplicate_invoice_attribute_flags_yet(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = generate_as(client, flag_setup, "owner")
    flag_types = {payload["flag_type"] for payload in response.json()}

    assert ControlFlagType.DUPLICATE_INVOICE_ATTRIBUTES.value not in flag_types


def test_owner_can_list_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "owner")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_reviewer_can_list_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "reviewer")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_viewer_can_list_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "viewer")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_non_member_cannot_list_control_flags(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_list_route_returns_only_flags_for_requested_document(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "owner", "second_document")
    payload = response.json()

    assert response.status_code == 200
    assert len(payload) == 1
    assert payload[0]["document_id"] == str(document_id_from(
        flag_setup,
        "second_document",
    ))


def test_list_route_does_not_leak_flags_from_another_document(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "owner", "flag_document")
    returned_ids = {item["id"] for item in response.json()}

    assert str(flag_id_from(flag_setup, "other_document_flag")) not in returned_ids


def test_list_route_does_not_leak_flags_through_cross_org_document(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        flags_url(
            organization_id_from(flag_setup),
            document_id_from(flag_setup, "other_document"),
        ),
        headers=auth_headers(token_for(flag_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_list_route_returns_safe_metadata(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "owner")

    assert response.status_code == 200
    for item in response.json():
        assert_safe_flag_payload(item)


def test_list_route_preserves_deterministic_service_ordering(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = list_as(client, flag_setup, "owner")
    severities = [item["severity"] for item in response.json()]

    assert severities == [
        ControlFlagSeverity.BLOCKER.value,
        ControlFlagSeverity.WARNING.value,
        ControlFlagSeverity.INFO.value,
    ]


def test_owner_can_read_control_flag_detail(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "owner")

    assert response.status_code == 200
    assert response.json()["id"] == str(flag_id_from(flag_setup))


def test_reviewer_can_read_control_flag_detail(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "reviewer")

    assert response.status_code == 200
    assert response.json()["id"] == str(flag_id_from(flag_setup))


def test_viewer_can_read_control_flag_detail(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "viewer")

    assert response.status_code == 200
    assert response.json()["id"] == str(flag_id_from(flag_setup))


def test_non_member_cannot_read_control_flag_detail(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_missing_control_flag_detail_returns_not_found(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response: Response = client.get(
        flag_detail_url(
            organization_id_from(flag_setup),
            document_id_from(flag_setup, "flag_document"),
            uuid.uuid4(),
        ),
        headers=auth_headers(token_for(flag_setup, "owner")),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Control flag was not found."


def test_control_flag_detail_scopes_by_document_id_and_flag_id(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(
        client,
        flag_setup,
        "owner",
        flag_key="other_document_flag",
        document_key="flag_document",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Control flag was not found."


def test_flag_from_another_document_is_not_returned(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(
        client,
        flag_setup,
        "owner",
        flag_key="other_document_flag",
        document_key="flag_document",
    )

    assert response.status_code == 404


def test_all_new_routes_appear_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    generate_path = (
        "/organizations/{organization_id}/documents/{document_id}"
        "/control-flags/generate"
    )
    list_path = (
        "/organizations/{organization_id}/documents/{document_id}/control-flags"
    )
    detail_path = (
        "/organizations/{organization_id}/documents/{document_id}"
        "/control-flags/{flag_id}"
    )

    assert generate_path in paths
    assert list_path in paths
    assert detail_path in paths


def test_control_flag_responses_do_not_include_local_absolute_paths(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "owner")
    serialized = response.text

    assert "stored_path" not in serialized
    assert "/tmp/" not in serialized
    assert "C:\\" not in serialized


def test_control_flag_responses_do_not_include_raw_passwords(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "owner")

    assert "safe password" not in response.text
    assert "password" not in response.text


def test_control_flag_responses_do_not_include_password_hashes(
    client: TestClient,
    flag_setup: dict[str, object],
) -> None:
    response = detail_as(client, flag_setup, "owner")

    assert "password_hash" not in response.text
    assert "$argon2" not in response.text


def test_control_flag_generation_creates_audit_entry(
    client: TestClient,
    flag_setup: dict[str, object],
    db_session: Session,
) -> None:
    owner = flag_setup["owner"]
    assert isinstance(owner, User)

    response = generate_as(client, flag_setup, "owner")

    assert response.status_code == 200
    generated_flags = response.json()
    audit_entry = db_session.scalars(select(AuditEntry)).all()[-1]
    assert audit_entry.action == AuditAction.CONTROL_FLAGS_GENERATED.value
    assert audit_entry.entity_type == AuditEntityType.DOCUMENT.value
    assert str(audit_entry.entity_id) == str(document_id_from(flag_setup))
    assert str(audit_entry.organization_id) == str(organization_id_from(flag_setup))
    assert audit_entry.actor_user_id == owner.id
    generated_flag_metadata = audit_entry.metadata_json["generated_flags"]
    assert isinstance(generated_flag_metadata, list)
    assert audit_entry.metadata_json["generated_flag_count"] == len(generated_flags)
    assert len(generated_flag_metadata) == len(generated_flags)


def test_control_flag_generation_zero_flags_still_creates_audit_entry(
    client: TestClient,
    flag_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = generate_as(client, flag_setup, "owner", "clean_document")

    assert response.status_code == 200
    assert response.json() == []
    audit_entry = db_session.scalars(select(AuditEntry)).all()[-1]
    assert audit_entry.action == AuditAction.CONTROL_FLAGS_GENERATED.value
    assert audit_entry.metadata_json["generated_flag_count"] == 0
    assert audit_entry.metadata_json["generated_flags"] == []


def test_viewer_denied_control_generation_does_not_create_audit_entry(
    client: TestClient,
    flag_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = generate_as(client, flag_setup, "viewer")

    assert response.status_code == 403
    assert db_session.scalars(select(AuditEntry)).all() == []
