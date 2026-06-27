"""Tests for Vault audit entry service behavior."""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.audit.actions import AuditAction
from vault.audit.entities import AuditEntityType
from vault.audit.models import AuditEntry
from vault.audit.service import (
    create_audit_entry,
    get_audit_entry,
    list_audit_entries,
    list_audit_entries_for_entity,
    require_audit_entry,
)
from vault.auth.models import User
from vault.auth.service import create_user
from vault.exceptions import AuditEntryNotFoundError, AuditEntryValidationError
from vault.models import Base
from vault.organizations.models import Organization
from vault.organizations.service import create_organization

SAFE_METADATA_EXAMPLE = {
    "document_status": "approved",
    "review_reason": "Invoice was checked against fake sample facts.",
    "stored_filename": "generated-document-id.pdf",
}


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
def actor(session: Session) -> User:
    return create_user(
        session,
        email="reviewer@example.com",
        raw_password="safe password",
        full_name="Reviewer Example",
    )


@pytest.fixture
def organization(session: Session, actor: User) -> Organization:
    return create_organization(
        session,
        creator=actor,
        name="Example Company",
    ).organization


def create_valid_audit_entry(
    session: Session,
    *,
    organization: Organization | None,
    actor: User | None,
    action: str = AuditAction.REVIEW_DECISION_CREATED.value,
    entity_type: str = AuditEntityType.REVIEW_DECISION.value,
    entity_id: uuid.UUID | None = None,
    summary: str = "Review decision was created.",
    metadata_json: dict[str, Any] | None = None,
) -> AuditEntry:
    metadata = SAFE_METADATA_EXAMPLE if metadata_json is None else metadata_json
    return create_audit_entry(
        session,
        organization_id=None if organization is None else organization.id,
        actor_user_id=None if actor is None else actor.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata_json=metadata,
    )


def test_create_audit_entry_stores_organization_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.organization_id == organization.id


def test_create_audit_entry_stores_actor_user_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.actor_user_id == actor.id


def test_create_audit_entry_stores_action(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.action == AuditAction.REVIEW_DECISION_CREATED.value


def test_create_audit_entry_stores_entity_type(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.entity_type == AuditEntityType.REVIEW_DECISION.value


def test_create_audit_entry_stores_entity_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entity_id = uuid.uuid4()
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_id=entity_id,
    )

    assert entry.entity_id == entity_id


def test_create_audit_entry_stores_summary(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        summary="Document status changed.",
    )

    assert entry.summary == "Document status changed."


def test_create_audit_entry_stores_metadata_json(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    metadata = {"old_status": "pending", "new_status": "approved"}
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        metadata_json=metadata,
    )

    assert entry.metadata_json == metadata


def test_omitted_metadata_stores_empty_object(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_audit_entry(
        session,
        organization_id=organization.id,
        actor_user_id=actor.id,
        action=AuditAction.ORGANIZATION_CREATED.value,
        entity_type=AuditEntityType.ORGANIZATION.value,
        entity_id=organization.id,
        summary="Organization was created.",
    )

    assert entry.metadata_json == {}


def test_create_audit_entry_gets_id_after_flush(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.id is not None


def test_create_audit_entry_does_not_commit_automatically(
    session: CommitTrackingSession,
    organization: Organization,
    actor: User,
) -> None:
    create_valid_audit_entry(session, organization=organization, actor=actor)

    assert session.commit_count == 0


def test_action_is_trimmed(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        action=f" {AuditAction.DOCUMENT_UPLOADED.value} ",
    )

    assert entry.action == AuditAction.DOCUMENT_UPLOADED.value


def test_entity_type_is_trimmed(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=f" {AuditEntityType.DOCUMENT.value} ",
    )

    assert entry.entity_type == AuditEntityType.DOCUMENT.value


def test_summary_is_trimmed(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        summary="  Document was uploaded.  ",
    )

    assert entry.summary == "Document was uploaded."


@pytest.mark.parametrize("action", ["", "   "])
def test_blank_action_is_rejected(
    session: Session,
    organization: Organization,
    actor: User,
    action: str,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_valid_audit_entry(
            session,
            organization=organization,
            actor=actor,
            action=action,
        )


@pytest.mark.parametrize("entity_type", ["", "   "])
def test_blank_entity_type_is_rejected(
    session: Session,
    organization: Organization,
    actor: User,
    entity_type: str,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_valid_audit_entry(
            session,
            organization=organization,
            actor=actor,
            entity_type=entity_type,
        )


@pytest.mark.parametrize("summary", ["", "   "])
def test_blank_summary_is_rejected(
    session: Session,
    organization: Organization,
    actor: User,
    summary: str,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_valid_audit_entry(
            session,
            organization=organization,
            actor=actor,
            summary=summary,
        )


def test_unsupported_action_is_rejected(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_valid_audit_entry(
            session,
            organization=organization,
            actor=actor,
            action="password_reset_requested",
        )


def test_unsupported_entity_type_is_rejected(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_valid_audit_entry(
            session,
            organization=organization,
            actor=actor,
            entity_type="session_token",
        )


def test_metadata_must_be_object_like(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    invalid_metadata: Any = ("not", "a", "mapping")
    with pytest.raises(AuditEntryValidationError):
        create_audit_entry(
            session,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action=AuditAction.USER_REGISTERED.value,
            entity_type=AuditEntityType.USER.value,
            summary="User was registered.",
            metadata_json=invalid_metadata,
        )


@pytest.mark.parametrize(
    "metadata_json",
    [
        ["not", "an", "object"],
        "not an object",
        123,
        True,
        None,
    ],
)
def test_metadata_non_objects_are_rejected(
    session: Session,
    organization: Organization,
    actor: User,
    metadata_json: Any,
) -> None:
    with pytest.raises(AuditEntryValidationError):
        create_audit_entry(
            session,
            organization_id=organization.id,
            actor_user_id=actor.id,
            action=AuditAction.USER_REGISTERED.value,
            entity_type=AuditEntityType.USER.value,
            summary="User was registered.",
            metadata_json=metadata_json,
        )


def test_create_audit_entry_copies_metadata_mapping(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    metadata = {"status": "approved"}
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        metadata_json=metadata,
    )
    metadata["status"] = "rejected"

    assert entry.metadata_json == {"status": "approved"}


def test_service_allows_nullable_organization_id(
    session: Session,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(session, organization=None, actor=actor)

    assert entry.organization_id is None


def test_service_allows_nullable_actor_user_id(
    session: Session,
    organization: Organization,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=None,
    )

    assert entry.actor_user_id is None


def test_service_allows_nullable_entity_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert entry.entity_id is None


def test_listing_audit_entries_returns_only_requested_organization(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    matching = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )
    other_organization = create_organization(
        session,
        creator=actor,
        name="Other Company",
    ).organization
    create_valid_audit_entry(
        session,
        organization=other_organization,
        actor=actor,
    )

    assert list_audit_entries(session, organization_id=organization.id) == [matching]


def test_listing_audit_entries_excludes_organization_null_entries(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    matching = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )
    create_valid_audit_entry(session, organization=None, actor=actor)

    assert list_audit_entries(session, organization_id=organization.id) == [matching]


def test_listing_audit_entries_has_deterministic_newest_first_ordering(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    oldest = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        summary="Oldest entry.",
    )
    newest = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        summary="Newest entry.",
    )
    middle = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        summary="Middle entry.",
    )
    oldest.created_at = datetime(2026, 1, 1, tzinfo=UTC)
    middle.created_at = datetime(2026, 1, 2, tzinfo=UTC)
    newest.created_at = datetime(2026, 1, 3, tzinfo=UTC)
    session.flush()

    assert list_audit_entries(session, organization_id=organization.id) == [
        newest,
        middle,
        oldest,
    ]


def test_listing_audit_entries_for_entity_scopes_by_type_and_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entity_id = uuid.uuid4()
    matching = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=entity_id,
    )
    create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=AuditEntityType.REVIEW_DECISION.value,
        entity_id=entity_id,
    )
    create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=uuid.uuid4(),
    )

    assert list_audit_entries_for_entity(
        session,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=entity_id,
    ) == [matching]


def test_entity_listing_does_not_return_another_entity_type(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entity_id = uuid.uuid4()
    create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=AuditEntityType.DOCUMENT_FACT.value,
        entity_id=entity_id,
    )

    assert list_audit_entries_for_entity(
        session,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=entity_id,
    ) == []


def test_entity_listing_does_not_return_another_entity_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=uuid.uuid4(),
    )

    assert list_audit_entries_for_entity(
        session,
        entity_type=AuditEntityType.DOCUMENT.value,
        entity_id=uuid.uuid4(),
    ) == []


def test_getting_audit_entry_scopes_by_organization_and_id(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(
        session,
        organization=organization,
        actor=actor,
    )

    assert get_audit_entry(
        session,
        organization_id=organization.id,
        audit_entry_id=entry.id,
    ) == entry


def test_requiring_missing_audit_entry_raises_safe_exception(
    session: Session,
    organization: Organization,
) -> None:
    with pytest.raises(AuditEntryNotFoundError):
        require_audit_entry(
            session,
            organization_id=organization.id,
            audit_entry_id=uuid.uuid4(),
        )


def test_audit_entry_from_another_organization_is_not_returned(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    other_organization = create_organization(
        session,
        creator=actor,
        name="Other Company",
    ).organization
    other_entry = create_valid_audit_entry(
        session,
        organization=other_organization,
        actor=actor,
    )

    assert get_audit_entry(
        session,
        organization_id=organization.id,
        audit_entry_id=other_entry.id,
    ) is None


def test_organization_null_audit_entry_is_not_returned_by_scoped_detail(
    session: Session,
    organization: Organization,
    actor: User,
) -> None:
    entry = create_valid_audit_entry(session, organization=None, actor=actor)

    assert get_audit_entry(
        session,
        organization_id=organization.id,
        audit_entry_id=entry.id,
    ) is None


def test_audit_metadata_examples_do_not_include_raw_passwords() -> None:
    text = str(SAFE_METADATA_EXAMPLE).lower()

    assert "password" not in text


def test_audit_metadata_examples_do_not_include_password_hashes() -> None:
    text = str(SAFE_METADATA_EXAMPLE).lower()

    assert "password_hash" not in text
    assert "argon2" not in text


def test_audit_metadata_examples_do_not_include_bearer_tokens() -> None:
    text = str(SAFE_METADATA_EXAMPLE).lower()

    assert "bearer" not in text
    assert "token" not in text


def test_audit_metadata_examples_do_not_include_local_absolute_paths() -> None:
    text = str(SAFE_METADATA_EXAMPLE)

    assert "C:\\" not in text
    assert "/home/" not in text
    assert "/Users/" not in text
