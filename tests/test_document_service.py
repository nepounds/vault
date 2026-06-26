"""Tests for Vault document metadata service behavior."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.documents.models import Document
from vault.documents.service import create_document_metadata
from vault.documents.statuses import DocumentStatus
from vault.exceptions import DocumentValidationError
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization

VALID_SHA256_HASH = "a" * 64
SECOND_SHA256_HASH = "b" * 64


class CommitTrackingSession(Session):
    """Test session that records unexpected commits."""

    commit_count: int

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.commit_count = 0

    def commit(self) -> None:
        self.commit_count += 1
        super().commit()


@pytest.fixture
def session() -> Iterator[CommitTrackingSession]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        class_=CommitTrackingSession,
        autoflush=False,
        autocommit=False,
    )

    with session_factory() as test_session:
        yield test_session


@pytest.fixture
def uploader(session: Session) -> User:
    return create_user(
        session,
        email="uploader@example.com",
        raw_password="safe password",
        full_name="Uploader Example",
    )


@pytest.fixture
def organization(session: Session, uploader: User) -> Organization:
    result = create_organization(
        session,
        creator=uploader,
        name="Example Company",
    )

    return result.organization


def create_valid_document(
    session: Session,
    *,
    organization: Organization,
    uploader: User,
    original_filename: str = "invoice.pdf",
    stored_filename: str = "safe-generated-name.pdf",
    content_type: str = "application/pdf",
    file_size_bytes: int = 1024,
    sha256_hash: str = VALID_SHA256_HASH,
) -> Document:
    return create_document_metadata(
        session,
        organization_id=organization.id,
        uploaded_by_user_id=uploader.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        file_size_bytes=file_size_bytes,
        sha256_hash=sha256_hash,
    )


def test_create_document_metadata_stores_organization_id(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert document.organization_id == organization.id


def test_create_document_metadata_stores_uploader_user_id(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert document.uploaded_by_user_id == uploader.id


def test_create_document_metadata_stores_original_filename(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        original_filename="  invoice.pdf  ",
    )

    assert document.original_filename == "invoice.pdf"


def test_create_document_metadata_stores_stored_filename(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        stored_filename="  safe-generated-name.pdf  ",
    )

    assert document.stored_filename == "safe-generated-name.pdf"


def test_create_document_metadata_stores_content_type(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        content_type="  application/pdf  ",
    )

    assert document.content_type == "application/pdf"


def test_create_document_metadata_stores_file_size(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        file_size_bytes=2048,
    )

    assert document.file_size_bytes == 2048


def test_create_document_metadata_stores_sha256_hash(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        sha256_hash=SECOND_SHA256_HASH,
    )

    assert document.sha256_hash == SECOND_SHA256_HASH


def test_created_document_status_defaults_to_pending(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert document.status == "pending"


def test_created_document_gets_id_after_flush(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert document.id is not None


def test_create_document_metadata_does_not_commit_automatically(
    session: CommitTrackingSession,
    organization: Organization,
    uploader: User,
) -> None:
    create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert session.commit_count == 0


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("original_filename", ""),
        ("original_filename", "   "),
        ("stored_filename", ""),
        ("stored_filename", "   "),
        ("content_type", ""),
        ("content_type", "   "),
        ("sha256_hash", ""),
        ("sha256_hash", "   "),
    ],
)
def test_create_document_metadata_rejects_blank_required_strings(
    session: Session,
    organization: Organization,
    uploader: User,
    field_name: str,
    field_value: str,
) -> None:
    values = {
        "original_filename": "invoice.pdf",
        "stored_filename": "safe-generated-name.pdf",
        "content_type": "application/pdf",
        "sha256_hash": VALID_SHA256_HASH,
    }
    values[field_name] = field_value

    with pytest.raises(DocumentValidationError, match=f"{field_name} is required"):
        create_document_metadata(
            session,
            organization_id=organization.id,
            uploaded_by_user_id=uploader.id,
            original_filename=values["original_filename"],
            stored_filename=values["stored_filename"],
            content_type=values["content_type"],
            file_size_bytes=1024,
            sha256_hash=values["sha256_hash"],
        )


@pytest.mark.parametrize(
    "sha256_hash",
    [
        "a" * 63,
        "a" * 65,
        "g" * 64,
        "A" * 64,
        "z" * 64,
    ],
)
def test_create_document_metadata_rejects_malformed_sha256_hash(
    session: Session,
    organization: Organization,
    uploader: User,
    sha256_hash: str,
) -> None:
    with pytest.raises(DocumentValidationError, match="sha256_hash must be 64"):
        create_valid_document(
            session,
            organization=organization,
            uploader=uploader,
            sha256_hash=sha256_hash,
        )


@pytest.mark.parametrize("file_size_bytes", [0, -1])
def test_create_document_metadata_rejects_non_positive_file_size(
    session: Session,
    organization: Organization,
    uploader: User,
    file_size_bytes: int,
) -> None:
    with pytest.raises(DocumentValidationError, match="file_size_bytes"):
        create_valid_document(
            session,
            organization=organization,
            uploader=uploader,
            file_size_bytes=file_size_bytes,
        )


def test_duplicate_sha256_hashes_are_allowed_for_now(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    first_document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        stored_filename="safe-generated-name-1.pdf",
    )
    second_document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
        stored_filename="safe-generated-name-2.pdf",
    )

    statement = select(Document).order_by(Document.stored_filename)
    documents = session.scalars(statement).all()

    assert documents == [first_document, second_document]
    assert first_document.sha256_hash == second_document.sha256_hash


def test_create_document_metadata_uses_official_pending_status_value(
    session: Session,
    organization: Organization,
    uploader: User,
) -> None:
    document = create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert document.status == DocumentStatus.PENDING.value


def test_create_document_metadata_creates_no_files_on_disk(
    session: Session,
    organization: Organization,
    uploader: User,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    work_dir = tmp_path / "metadata-service"
    work_dir.mkdir()
    monkeypatch.chdir(work_dir)

    create_valid_document(
        session,
        organization=organization,
        uploader=uploader,
    )

    assert list(work_dir.iterdir()) == []
