"""Tests for Vault review decision API routes."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from vault.api.dependencies import get_database_session
from vault.api.main import create_app
from vault.auth.models import User
from vault.auth.service import create_user
from vault.auth.tokens import create_access_token
from vault.documents.models import Document
from vault.documents.service import create_document_metadata
from vault.documents.statuses import DocumentStatus
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization
from vault.reviews.decisions import ReviewDecisionValueEnum
from vault.reviews.models import ReviewDecision
from vault.reviews.service import create_review_decision

VALID_SHA256_HASH = "a" * 64
SECOND_SHA256_HASH = "b" * 64
THIRD_SHA256_HASH = "c" * 64
OTHER_SHA256_HASH = "d" * 64
SAFE_REVIEW_KEYS = {
    "id",
    "document_id",
    "reviewer_user_id",
    "decision",
    "reason",
    "created_at",
}


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for review route tests."""
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
    """Create a test user for review decision API tests."""
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
    """Create document metadata for review decision API tests."""
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
def review_setup(db_session: Session) -> dict[str, object]:
    """Create users, organizations, documents, and starter reviews."""
    owner = create_api_user(
        db_session,
        email="review-owner@example.com",
        full_name="Review Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="reviewer@example.com",
        full_name="Review Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="review-viewer@example.com",
        full_name="Review Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="review-outsider@example.com",
        full_name="Review Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="review-inactive@example.com",
        full_name="Review Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Review Company",
    )
    other_created = create_organization(
        db_session,
        creator=outsider,
        name="Other Review Company",
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
    no_review_document = create_api_document(
        db_session,
        organization_id=created.organization.id,
        uploaded_by_user_id=owner.id,
        original_filename="empty.pdf",
        stored_filename="generated-empty.pdf",
        sha256_hash=THIRD_SHA256_HASH,
    )
    other_document = create_api_document(
        db_session,
        organization_id=other_created.organization.id,
        uploaded_by_user_id=outsider.id,
        original_filename="other.pdf",
        stored_filename="generated-other.pdf",
        sha256_hash=OTHER_SHA256_HASH,
    )
    first_review = create_review_decision(
        db_session,
        document_id=document.id,
        reviewer_user_id=owner.id,
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="Initial approval.",
    )
    second_review = create_review_decision(
        db_session,
        document_id=document.id,
        reviewer_user_id=reviewer.id,
        decision=ReviewDecisionValueEnum.NEEDS_INFO.value,
        reason="Need one extra detail.",
    )
    other_doc_review = create_review_decision(
        db_session,
        document_id=second_document.id,
        reviewer_user_id=reviewer.id,
        decision=ReviewDecisionValueEnum.REJECTED.value,
        reason="Different document.",
    )
    other_org_review = create_review_decision(
        db_session,
        document_id=other_document.id,
        reviewer_user_id=outsider.id,
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="Other organization.",
    )
    first_review.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    second_review.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    other_doc_review.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    other_org_review.created_at = datetime(2026, 1, 4, tzinfo=UTC)
    db_session.commit()
    return {
        "owner": owner,
        "reviewer": reviewer,
        "viewer": viewer,
        "outsider": outsider,
        "inactive_user": inactive_user,
        "organization_id": created.organization.id,
        "other_organization_id": other_created.organization.id,
        "document": document,
        "second_document": second_document,
        "no_review_document": no_review_document,
        "other_document": other_document,
        "first_review": first_review,
        "second_review": second_review,
        "other_doc_review": other_doc_review,
        "other_org_review": other_org_review,
    }


def token_for(user: User, *, minutes: int = 60) -> str:
    """Create an authorization token for a test user."""
    return create_access_token(
        user.id,
        expires_delta=timedelta(minutes=minutes),
    )


def auth_header(user: User, *, minutes: int = 60) -> dict[str, str]:
    """Create an authorization header for a test user."""
    return {"Authorization": f"Bearer {token_for(user, minutes=minutes)}"}


def submit_review(
    client: TestClient,
    *,
    organization_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User,
    decision: str = ReviewDecisionValueEnum.APPROVED.value,
    reason: str = "Looks good.",
) -> Response:
    """Submit one review decision through the API."""
    return cast(
        Response,
        client.post(
            f"/organizations/{organization_id}/documents/{document_id}/review",
            headers=auth_header(user),
            json={"decision": decision, "reason": reason},
        ),
    )


def list_reviews(
    client: TestClient,
    *,
    organization_id: uuid.UUID,
    document_id: uuid.UUID,
    user: User,
) -> Response:
    """List review decisions through the API."""
    return cast(
        Response,
        client.get(
            f"/organizations/{organization_id}/documents/{document_id}/reviews",
            headers=auth_header(user),
        ),
    )


def read_review(
    client: TestClient,
    *,
    organization_id: uuid.UUID,
    document_id: uuid.UUID,
    review_decision_id: uuid.UUID,
    user: User,
) -> Response:
    """Read review decision detail through the API."""
    return cast(
        Response,
        client.get(
            "/organizations/"
            f"{organization_id}/documents/{document_id}/reviews/"
            f"{review_decision_id}",
            headers=auth_header(user),
        ),
    )


def test_owner_can_submit_approved_review_decision(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 201
    assert response.json()["decision"] == ReviewDecisionValueEnum.APPROVED.value


def test_reviewer_can_submit_approved_review_decision(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["reviewer"]),
    )

    assert response.status_code == 201


def test_viewer_cannot_submit_review_decision(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["viewer"]),
    )

    assert response.status_code == 403


def test_non_member_cannot_submit_review_decision(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["outsider"]),
    )

    assert response.status_code == 403


def test_missing_token_returns_401_for_submit(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    response = client.post(
        "/organizations/"
        f"{review_setup['organization_id']}/documents/{document.id}/review",
        json={"decision": "approved", "reason": "Looks good."},
    )

    assert response.status_code == 401


def test_invalid_token_returns_401_for_submit(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    response = client.post(
        "/organizations/"
        f"{review_setup['organization_id']}/documents/{document.id}/review",
        headers={"Authorization": "Bearer not-a-valid-token"},
        json={"decision": "approved", "reason": "Looks good."},
    )

    assert response.status_code == 401


def test_expired_token_returns_401_for_submit(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    owner = cast(User, review_setup["owner"])
    response = client.post(
        "/organizations/"
        f"{review_setup['organization_id']}/documents/{document.id}/review",
        headers=auth_header(owner, minutes=-1),
        json={"decision": "approved", "reason": "Looks good."},
    )

    assert response.status_code == 401


def test_inactive_user_token_returns_401_for_submit(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["inactive_user"]),
    )

    assert response.status_code == 401


def test_unknown_organization_returns_safe_403_for_submit(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=uuid.uuid4(),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 403


def test_submit_route_rejects_document_from_another_organization(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["other_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404


def test_submit_route_verifies_document_belongs_to_path_organization(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["other_organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        user=cast(User, review_setup["outsider"]),
    )

    assert response.status_code == 404


def test_missing_document_in_accessible_organization_returns_404(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=uuid.uuid4(),
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Document was not found."


def test_submit_route_returns_safe_review_decision_metadata(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
        reason="Reviewed safely.",
    )

    payload = response.json()
    assert set(payload) == SAFE_REVIEW_KEYS
    assert payload["reason"] == "Reviewed safely."


def test_submit_route_persists_review_decision_row(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["reviewer"]),
        reason="Persistent review.",
    )

    review_id = uuid.UUID(response.json()["id"])
    persisted = db_session.get(ReviewDecision, review_id)
    assert persisted is not None


def test_persisted_review_row_stores_expected_fields(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    reviewer = cast(User, review_setup["reviewer"])
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=document.id,
        user=reviewer,
        decision=ReviewDecisionValueEnum.REJECTED.value,
        reason="Incorrect amount.",
    )

    persisted = db_session.get(ReviewDecision, uuid.UUID(response.json()["id"]))
    assert persisted is not None
    assert persisted.id is not None
    assert persisted.created_at is not None
    assert persisted.document_id == document.id
    assert persisted.reviewer_user_id == reviewer.id
    assert persisted.decision == ReviewDecisionValueEnum.REJECTED.value
    assert persisted.reason == "Incorrect amount."


@pytest.mark.parametrize(
    ("decision", "expected_status"),
    [
        (ReviewDecisionValueEnum.APPROVED.value, DocumentStatus.APPROVED.value),
        (ReviewDecisionValueEnum.REJECTED.value, DocumentStatus.REJECTED.value),
        (ReviewDecisionValueEnum.NEEDS_INFO.value, DocumentStatus.NEEDS_INFO.value),
    ],
)
def test_review_decision_updates_document_status(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
    decision: str,
    expected_status: str,
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=document.id,
        user=cast(User, review_setup["owner"]),
        decision=decision,
        reason="Status transition reason.",
    )

    db_session.refresh(document)
    assert document.status == expected_status


@pytest.mark.parametrize(
    ("decision", "reason"),
    [
        ("", "Valid reason."),
        ("approved", ""),
        ("approved", "   "),
        ("unsupported", "Valid reason."),
        (DocumentStatus.PENDING.value, "Valid reason."),
        ("approved", ""),
        ("rejected", ""),
        ("needs_info", ""),
    ],
)
def test_submit_route_rejects_invalid_review_input(
    client: TestClient,
    review_setup: dict[str, object],
    decision: str,
    reason: str,
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
        decision=decision,
        reason=reason,
    )

    assert response.status_code == 400


def test_multiple_review_decisions_for_same_document_are_allowed(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    for reason in ["First decision.", "Second decision."]:
        submit_review(
            client,
            organization_id=cast(uuid.UUID, review_setup["organization_id"]),
            document_id=document.id,
            user=cast(User, review_setup["owner"]),
            reason=reason,
        )

    rows = db_session.scalars(
        select(ReviewDecision).where(ReviewDecision.document_id == document.id)
    ).all()
    assert len(rows) == 2


def test_later_review_decisions_update_document_status_again(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
) -> None:
    document = cast(Document, review_setup["no_review_document"])
    submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=document.id,
        user=cast(User, review_setup["owner"]),
        decision=ReviewDecisionValueEnum.APPROVED.value,
        reason="Approved first.",
    )
    submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=document.id,
        user=cast(User, review_setup["reviewer"]),
        decision=ReviewDecisionValueEnum.NEEDS_INFO.value,
        reason="Needs more info later.",
    )

    db_session.refresh(document)
    assert document.status == DocumentStatus.NEEDS_INFO.value


@pytest.mark.parametrize("role_name", ["owner", "reviewer", "viewer"])
def test_members_can_list_review_decisions(
    client: TestClient,
    review_setup: dict[str, object],
    role_name: str,
) -> None:
    response = list_reviews(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        user=cast(User, review_setup[role_name]),
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_non_member_cannot_list_review_decisions(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = list_reviews(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        user=cast(User, review_setup["outsider"]),
    )

    assert response.status_code == 403


def test_list_route_returns_only_reviews_for_requested_document(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = list_reviews(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    review_ids = {item["id"] for item in response.json()}
    assert str(cast(ReviewDecision, review_setup["first_review"]).id) in review_ids
    assert str(cast(ReviewDecision, review_setup["second_review"]).id) in review_ids
    other_review_id = str(
        cast(ReviewDecision, review_setup["other_doc_review"]).id
    )
    assert other_review_id not in review_ids


def test_list_route_does_not_leak_cross_organization_reviews(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = list_reviews(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["other_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404


def test_list_route_returns_safe_metadata_and_ordering(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = list_reviews(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        user=cast(User, review_setup["viewer"]),
    )

    payload = response.json()
    assert [item["reason"] for item in payload] == [
        "Initial approval.",
        "Need one extra detail.",
    ]
    assert all(set(item) == SAFE_REVIEW_KEYS for item in payload)


@pytest.mark.parametrize("role_name", ["owner", "reviewer", "viewer"])
def test_members_can_read_review_decision_detail(
    client: TestClient,
    review_setup: dict[str, object],
    role_name: str,
) -> None:
    response = read_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        review_decision_id=cast(ReviewDecision, review_setup["first_review"]).id,
        user=cast(User, review_setup[role_name]),
    )

    assert response.status_code == 200
    assert response.json()["reason"] == "Initial approval."


def test_non_member_cannot_read_review_decision_detail(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = read_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        review_decision_id=cast(ReviewDecision, review_setup["first_review"]).id,
        user=cast(User, review_setup["outsider"]),
    )

    assert response.status_code == 403


def test_missing_review_decision_detail_returns_404(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = read_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        review_decision_id=uuid.uuid4(),
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Review decision was not found."


def test_review_detail_scopes_by_document_id_and_review_decision_id(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = read_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["second_document"]).id,
        review_decision_id=cast(ReviewDecision, review_setup["first_review"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404


def test_review_decision_from_another_document_is_not_returned(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = read_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["document"]).id,
        review_decision_id=cast(ReviewDecision, review_setup["other_doc_review"]).id,
        user=cast(User, review_setup["owner"]),
    )

    assert response.status_code == 404


def test_all_new_review_routes_appear_in_openapi(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/organizations/{organization_id}/documents/{document_id}/review" in paths
    assert "/organizations/{organization_id}/documents/{document_id}/reviews" in paths
    assert (
        "/organizations/{organization_id}/documents/{document_id}"
        "/reviews/{review_decision_id}"
        in paths
    )


def test_review_responses_do_not_include_unsafe_fields(
    client: TestClient,
    review_setup: dict[str, object],
) -> None:
    response = submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    response_text = response.text.lower()
    assert "/" not in response.json()
    assert "password" not in response_text
    assert "password_hash" not in response_text
    assert "token" not in response_text
    assert "generated-empty.pdf" not in response_text


def test_review_routes_do_not_create_audit_entries_yet(
    client: TestClient,
    db_session: Session,
    review_setup: dict[str, object],
) -> None:
    submit_review(
        client,
        organization_id=cast(uuid.UUID, review_setup["organization_id"]),
        document_id=cast(Document, review_setup["no_review_document"]).id,
        user=cast(User, review_setup["owner"]),
    )

    inspector = inspect(db_session.get_bind())
    assert "audit_entries" not in inspector.get_table_names()
