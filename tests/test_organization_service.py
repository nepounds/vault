"""Tests for Vault organization creation service behavior."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.exceptions import OrganizationValidationError
from vault.models import Base
from vault.organizations.models import Membership, Organization
from vault.organizations.roles import MembershipRole
from vault.organizations.service import create_organization


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
def creator(session: Session) -> User:
    return create_user(
        session,
        email="owner@example.com",
        raw_password="safe password",
        full_name="Owner Example",
    )


def test_create_organization_stores_trimmed_name(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="  Example Company  ",
    )

    assert result.organization.name == "Example Company"


def test_create_organization_stores_creator_user_id(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    assert result.organization.created_by_user_id == creator.id


def test_create_organization_creates_owner_membership_for_creator(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    membership = session.scalar(select(Membership))

    assert membership is result.membership
    assert result.membership.organization_id == result.organization.id
    assert result.membership.user_id == creator.id


def test_create_organization_uses_official_owner_role(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    assert result.membership.role == MembershipRole.OWNER.value


def test_create_organization_returns_ids_after_flush(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    assert result.organization.id is not None
    assert result.membership.id is not None


def test_create_organization_rejects_blank_name(
    session: Session,
    creator: User,
) -> None:
    with pytest.raises(OrganizationValidationError, match="name is required"):
        create_organization(session, creator=creator, name="")


def test_create_organization_rejects_whitespace_only_name(
    session: Session,
    creator: User,
) -> None:
    with pytest.raises(OrganizationValidationError, match="name is required"):
        create_organization(session, creator=creator, name="   ")


def test_create_organization_rejects_inactive_creator(
    session: Session,
    creator: User,
) -> None:
    creator.is_active = False
    session.flush()

    with pytest.raises(OrganizationValidationError, match="inactive users"):
        create_organization(
            session,
            creator=creator,
            name="Example Company",
        )


def test_create_organization_does_not_commit_automatically(
    session: CommitTrackingSession,
    creator: User,
) -> None:
    create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    assert session.commit_count == 0


def test_create_organization_and_membership_use_same_session(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    organizations = session.scalars(select(Organization)).all()
    memberships = session.scalars(select(Membership)).all()

    assert organizations == [result.organization]
    assert memberships == [result.membership]


def test_duplicate_membership_constraint_still_rejects_duplicates(
    session: Session,
    creator: User,
) -> None:
    result = create_organization(
        session,
        creator=creator,
        name="Example Company",
    )

    duplicate = Membership()
    duplicate.organization_id = result.organization.id
    duplicate.user_id = creator.id
    duplicate.role = MembershipRole.OWNER.value
    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.flush()
