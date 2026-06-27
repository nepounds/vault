"""Tests for the Vault document upload API."""

from __future__ import annotations

import hashlib
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
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
from vault.documents.models import Document
from vault.documents.statuses import DocumentStatus
from vault.documents.validation import MAX_UPLOAD_SIZE_BYTES
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization

VALID_CSV_BYTES = b"vendor,amount\nExample Vendor,12.34\n"


@pytest.fixture
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Configure uploads to use a temporary test directory."""
    directory = tmp_path / "uploads"
    monkeypatch.setenv("VAULT_UPLOAD_DIR", str(directory))
    return directory


@pytest.fixture
def session_factory() -> sessionmaker[Session]:
    """Create an isolated SQLite session factory for upload route tests."""
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
    upload_dir: Path,
) -> Iterator[TestClient]:
    """Create a test client with database and upload-dir isolation."""
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


def create_api_user(
    session: Session,
    *,
    email: str,
    full_name: str,
    is_active: bool = True,
) -> User:
    """Create a test user for document upload API tests."""
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


@pytest.fixture
def upload_setup(db_session: Session) -> dict[str, object]:
    """Create users, one organization, and upload-related memberships."""
    owner = create_api_user(
        db_session,
        email="upload-owner@example.com",
        full_name="Upload Owner",
    )
    reviewer = create_api_user(
        db_session,
        email="upload-reviewer@example.com",
        full_name="Upload Reviewer",
    )
    viewer = create_api_user(
        db_session,
        email="upload-viewer@example.com",
        full_name="Upload Viewer",
    )
    outsider = create_api_user(
        db_session,
        email="upload-outsider@example.com",
        full_name="Upload Outsider",
    )
    inactive_user = create_api_user(
        db_session,
        email="upload-inactive@example.com",
        full_name="Upload Inactive",
        is_active=False,
    )
    created = create_organization(
        db_session,
        creator=owner,
        name="Upload Company",
    )
    reviewer_membership = add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )
    viewer_membership = add_membership(
        db_session,
        organization_id=created.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )
    db_session.commit()
    return {
        "organization_id": created.organization.id,
        "owner": owner,
        "reviewer": reviewer,
        "viewer": viewer,
        "outsider": outsider,
        "inactive_user": inactive_user,
        "owner_membership": created.membership,
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


def auth_headers(token: str) -> dict[str, str]:
    """Return an Authorization header for a bearer token."""
    return {"Authorization": f"Bearer {token}"}


def csv_upload(
    filename: str = "invoice.csv",
    content: bytes = VALID_CSV_BYTES,
    content_type: str = "text/csv",
) -> dict[str, tuple[str, bytes, str]]:
    """Build a multipart file payload for the upload route."""
    return {"file": (filename, content, content_type)}


def upload_url(organization_id: uuid.UUID) -> str:
    return f"/organizations/{organization_id}/documents/upload"


def upload_as(
    client: TestClient,
    setup: dict[str, object],
    user_key: str,
    files: dict[str, tuple[str, bytes, str]] | None = None,
) -> Response:
    organization_id = organization_id_from(setup)
    response = client.post(
        upload_url(organization_id),
        headers=auth_headers(token_for(setup, user_key)),
        files=csv_upload() if files is None else files,
    )
    return cast(Response, response)


def latest_document(session: Session) -> Document:
    document = session.scalar(select(Document))
    assert document is not None
    return document


def test_owner_can_upload_valid_csv_file(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "owner")

    assert response.status_code == 201


def test_reviewer_can_upload_valid_csv_file(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "reviewer")

    assert response.status_code == 201


def test_viewer_cannot_upload(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "viewer")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_non_member_cannot_upload(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "outsider")

    assert response.status_code == 403
    assert response.json()["detail"] == "Organization access is not available."


def test_unknown_organization_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = client.post(
        upload_url(uuid.uuid4()),
        headers=auth_headers(token_for(upload_setup, "owner")),
        files=csv_upload(),
    )

    assert response.status_code == 403


def test_missing_token_returns_unauthorized(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = client.post(
        upload_url(organization_id_from(upload_setup)),
        files=csv_upload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_invalid_token_returns_unauthorized(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = client.post(
        upload_url(organization_id_from(upload_setup)),
        headers=auth_headers("not-a-token"),
        files=csv_upload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_expired_token_returns_unauthorized(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    owner = upload_setup["owner"]
    assert isinstance(owner, User)
    token = create_access_token(
        owner.id,
        expires_delta=timedelta(minutes=-1),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )

    response = client.post(
        upload_url(organization_id_from(upload_setup)),
        headers=auth_headers(token),
        files=csv_upload(),
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_inactive_user_token_returns_unauthorized(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "inactive_user")

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials."


def test_successful_upload_returns_safe_document_metadata(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    owner = upload_setup["owner"]
    assert isinstance(owner, User)

    response = upload_as(client, upload_setup, "owner")

    body = response.json()
    assert response.status_code == 201
    assert body["id"]
    assert body["organization_id"] == str(organization_id_from(upload_setup))
    assert body["uploaded_by_user_id"] == str(owner.id)
    assert body["original_filename"] == "invoice.csv"
    assert body["stored_filename"].endswith(".csv")
    assert body["stored_filename"] != "invoice.csv"
    assert body["content_type"] == "text/csv"
    assert body["file_size_bytes"] == len(VALID_CSV_BYTES)
    assert body["sha256_hash"] == hashlib.sha256(VALID_CSV_BYTES).hexdigest()
    assert body["status"] == DocumentStatus.PENDING.value
    assert body["created_at"]


def test_response_does_not_include_local_absolute_stored_path(
    client: TestClient,
    upload_setup: dict[str, object],
    upload_dir: Path,
) -> None:
    response = upload_as(client, upload_setup, "owner")

    body = response.json()
    assert "stored_path" not in body
    assert str(upload_dir) not in str(body)


def test_response_does_not_include_raw_passwords_or_hashes(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(client, upload_setup, "owner")

    response_text = response.text.lower()
    assert "safe password" not in response_text
    assert "password_hash" not in response_text


def test_successful_upload_creates_document_row(
    client: TestClient,
    upload_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = upload_as(client, upload_setup, "owner")

    document = latest_document(db_session)
    assert response.status_code == 201
    assert str(document.id) == response.json()["id"]


def test_document_row_stores_expected_metadata(
    client: TestClient,
    upload_setup: dict[str, object],
    db_session: Session,
) -> None:
    owner = upload_setup["owner"]
    assert isinstance(owner, User)

    response = upload_as(client, upload_setup, "owner")

    document = latest_document(db_session)
    assert response.status_code == 201
    assert document.organization_id == organization_id_from(upload_setup)
    assert document.uploaded_by_user_id == owner.id
    assert document.original_filename == "invoice.csv"
    assert document.stored_filename.endswith(".csv")
    assert document.stored_filename != "invoice.csv"
    assert document.content_type == "text/csv"
    assert document.file_size_bytes == len(VALID_CSV_BYTES)
    assert document.sha256_hash == hashlib.sha256(VALID_CSV_BYTES).hexdigest()
    assert document.status == DocumentStatus.PENDING.value


def test_uploaded_bytes_are_written_under_configured_upload_directory(
    client: TestClient,
    upload_setup: dict[str, object],
    upload_dir: Path,
) -> None:
    response = upload_as(client, upload_setup, "owner")

    stored_filename = response.json()["stored_filename"]
    stored_path = upload_dir / stored_filename
    assert stored_path.is_file()
    assert stored_path.read_bytes() == VALID_CSV_BYTES


def test_uploaded_bytes_are_not_written_using_original_filename_as_path(
    client: TestClient,
    upload_setup: dict[str, object],
    upload_dir: Path,
) -> None:
    response = upload_as(client, upload_setup, "owner")

    assert response.status_code == 201
    assert not (upload_dir / "invoice.csv").exists()


def test_invalid_extension_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(filename="invoice.exe"),
    )

    assert response.status_code == 400


def test_invalid_content_type_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(content_type="application/octet-stream"),
    )

    assert response.status_code == 400


def test_mismatched_extension_and_content_type_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(filename="invoice.pdf", content_type="text/csv"),
    )

    assert response.status_code == 400


def test_empty_upload_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(content=b""),
    )

    assert response.status_code == 400


def test_oversized_upload_is_rejected(
    client: TestClient,
    upload_setup: dict[str, object],
) -> None:
    oversized_bytes = b"a" * (MAX_UPLOAD_SIZE_BYTES + 1)

    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(content=oversized_bytes),
    )

    assert response.status_code == 400


def test_upload_route_appears_in_openapi(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/organizations/{organization_id}/documents/upload" in response.json()[
        "paths"
    ]


def test_upload_creates_safe_document_uploaded_audit_entry(
    client: TestClient,
    upload_setup: dict[str, object],
    db_session: Session,
    upload_dir: Path,
) -> None:
    owner = upload_setup["owner"]
    assert isinstance(owner, User)

    response = upload_as(client, upload_setup, "owner")

    assert response.status_code == 201
    document_id = response.json()["id"]
    audit_entry = db_session.scalar(select(AuditEntry))
    assert audit_entry is not None
    assert audit_entry.action == AuditAction.DOCUMENT_UPLOADED.value
    assert audit_entry.entity_type == AuditEntityType.DOCUMENT.value
    assert str(audit_entry.organization_id) == str(organization_id_from(upload_setup))
    assert str(audit_entry.entity_id) == document_id
    assert audit_entry.actor_user_id == owner.id
    assert audit_entry.metadata_json["original_filename"] == "invoice.csv"
    assert audit_entry.metadata_json["content_type"] == "text/csv"
    assert audit_entry.metadata_json["file_size_bytes"] == len(VALID_CSV_BYTES)
    assert audit_entry.metadata_json["status"] == DocumentStatus.PENDING.value
    metadata_text = str(audit_entry.metadata_json)
    assert str(upload_dir) not in metadata_text
    assert "stored_path" not in metadata_text


def test_viewer_denied_upload_does_not_create_audit_entry(
    client: TestClient,
    upload_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = upload_as(client, upload_setup, "viewer")

    assert response.status_code == 403
    assert db_session.scalars(select(AuditEntry)).all() == []


def test_failed_upload_validation_does_not_create_audit_entry(
    client: TestClient,
    upload_setup: dict[str, object],
    db_session: Session,
) -> None:
    response = upload_as(
        client,
        upload_setup,
        "owner",
        files=csv_upload(filename="bad.exe", content_type="text/csv"),
    )

    assert response.status_code == 400
    assert db_session.scalars(select(AuditEntry)).all() == []
