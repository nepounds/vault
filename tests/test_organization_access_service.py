"""Tests for organization membership access service helpers."""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from vault.auth.models import User
from vault.auth.service import create_user
from vault.exceptions import (
    OrganizationMembershipRequiredError,
    OrganizationRoleRequiredError,
)
from vault.models import Base
from vault.organizations.models import Membership
from vault.organizations.roles import ROLE_VALUES, MembershipRole
from vault.organizations.service import (
    create_organization,
    get_membership_for_user,
    membership_has_role,
    require_membership,
    require_membership_role,
)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
    )

    with session_factory() as test_session:
        yield test_session


@pytest.fixture
def owner(session: Session) -> User:
    return create_user(
        session,
        email="owner-access@example.com",
        raw_password="safe password",
        full_name="Owner Access",
    )


@pytest.fixture
def reviewer(session: Session) -> User:
    return create_user(
        session,
        email="reviewer-access@example.com",
        raw_password="safe password",
        full_name="Reviewer Access",
    )


@pytest.fixture
def viewer(session: Session) -> User:
    return create_user(
        session,
        email="viewer-access@example.com",
        raw_password="safe password",
        full_name="Viewer Access",
    )


@pytest.fixture
def outsider(session: Session) -> User:
    return create_user(
        session,
        email="outsider-access@example.com",
        raw_password="safe password",
        full_name="Outsider Access",
    )


def add_membership(
    session: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MembershipRole,
) -> Membership:
    membership = Membership()
    membership.organization_id = organization_id
    membership.user_id = user_id
    membership.role = role.value
    session.add(membership)
    session.flush()
    return membership


def test_membership_lookup_returns_membership_for_member(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(
        session,
        creator=owner,
        name="Example Company",
    )

    membership = get_membership_for_user(
        session,
        organization_id=result.organization.id,
        user_id=owner.id,
    )

    assert membership is result.membership


def test_membership_lookup_returns_none_for_non_member(
    session: Session,
    owner: User,
    outsider: User,
) -> None:
    result = create_organization(
        session,
        creator=owner,
        name="Example Company",
    )

    membership = get_membership_for_user(
        session,
        organization_id=result.organization.id,
        user_id=outsider.id,
    )

    assert membership is None


def test_required_membership_returns_membership_for_member(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(
        session,
        creator=owner,
        name="Example Company",
    )

    membership = require_membership(
        session,
        organization_id=result.organization.id,
        user_id=owner.id,
    )

    assert membership is result.membership


def test_required_membership_raises_for_non_member(
    session: Session,
    owner: User,
    outsider: User,
) -> None:
    result = create_organization(
        session,
        creator=owner,
        name="Example Company",
    )

    with pytest.raises(OrganizationMembershipRequiredError):
        require_membership(
            session,
            organization_id=result.organization.id,
            user_id=outsider.id,
        )


def test_required_membership_raises_for_unknown_organization(
    session: Session,
    owner: User,
) -> None:
    with pytest.raises(OrganizationMembershipRequiredError):
        require_membership(
            session,
            organization_id=uuid.uuid4(),
            user_id=owner.id,
        )


def test_role_check_succeeds_for_allowed_owner_role(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")

    assert membership_has_role(
        result.membership,
        [MembershipRole.OWNER],
    )


def test_role_check_succeeds_for_allowed_reviewer_role(
    session: Session,
    owner: User,
    reviewer: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")
    membership = add_membership(
        session,
        organization_id=result.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )

    assert membership_has_role(
        membership,
        [MembershipRole.REVIEWER],
    )


def test_role_check_succeeds_for_allowed_viewer_role(
    session: Session,
    owner: User,
    viewer: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")
    membership = add_membership(
        session,
        organization_id=result.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )

    assert membership_has_role(
        membership,
        [MembershipRole.VIEWER],
    )


def test_role_check_fails_when_role_is_not_allowed(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")

    assert not membership_has_role(
        result.membership,
        [MembershipRole.REVIEWER],
    )


def test_owner_is_not_automatically_allowed_for_reviewer_access(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")

    with pytest.raises(OrganizationRoleRequiredError):
        require_membership_role(
            session,
            organization_id=result.organization.id,
            user_id=owner.id,
            allowed_roles=[MembershipRole.REVIEWER],
        )


def test_reviewer_is_not_automatically_allowed_for_owner_access(
    session: Session,
    owner: User,
    reviewer: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")
    add_membership(
        session,
        organization_id=result.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )

    with pytest.raises(OrganizationRoleRequiredError):
        require_membership_role(
            session,
            organization_id=result.organization.id,
            user_id=reviewer.id,
            allowed_roles=[MembershipRole.OWNER],
        )


def test_viewer_is_not_allowed_when_owner_or_reviewer_is_required(
    session: Session,
    owner: User,
    viewer: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")
    add_membership(
        session,
        organization_id=result.organization.id,
        user_id=viewer.id,
        role=MembershipRole.VIEWER,
    )

    with pytest.raises(OrganizationRoleRequiredError):
        require_membership_role(
            session,
            organization_id=result.organization.id,
            user_id=viewer.id,
            allowed_roles=[MembershipRole.OWNER, MembershipRole.REVIEWER],
        )


def test_multiple_allowed_roles_work(
    session: Session,
    owner: User,
    reviewer: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")
    membership = add_membership(
        session,
        organization_id=result.organization.id,
        user_id=reviewer.id,
        role=MembershipRole.REVIEWER,
    )

    allowed_membership = require_membership_role(
        session,
        organization_id=result.organization.id,
        user_id=reviewer.id,
        allowed_roles=[MembershipRole.OWNER, MembershipRole.REVIEWER],
    )

    assert allowed_membership is membership


def test_unknown_allowed_role_values_fail_closed(
    session: Session,
    owner: User,
) -> None:
    result = create_organization(session, creator=owner, name="Example Company")

    assert not membership_has_role(result.membership, ["admin"])


def test_unknown_membership_role_values_fail_closed() -> None:
    membership = Membership()
    membership.role = "admin"

    assert not membership_has_role(membership, [MembershipRole.OWNER])


def test_helpers_use_official_role_values() -> None:
    assert tuple(role.value for role in MembershipRole) == ROLE_VALUES
