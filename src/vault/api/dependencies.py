"""Shared FastAPI dependencies for Vault routes."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.auth.service import load_active_user_from_token
from vault.database import (
    create_engine_from_environment,
    create_session_factory,
)
from vault.exceptions import AuthenticationError, OrganizationAccessError
from vault.organizations.models import Membership
from vault.organizations.roles import MembershipRole
from vault.organizations.service import require_membership_role

_bearer_scheme = HTTPBearer(auto_error=False)


def get_database_session() -> Iterator[Session]:
    """Yield a SQLAlchemy session and close it safely after the request."""
    engine = create_engine_from_environment()
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    session: Annotated[Session, Depends(get_database_session)],
) -> User:
    """Return the active user identified by a valid bearer access token."""
    if credentials is None:
        raise _unauthorized_error()

    token = credentials.credentials.strip()
    if credentials.scheme.lower() != "bearer" or not token:
        raise _unauthorized_error()

    try:
        return load_active_user_from_token(session, token)
    except AuthenticationError as exc:
        raise _unauthorized_error() from exc


def _unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_organization_roles(
    *allowed_roles: MembershipRole,
) -> Callable[..., Membership]:
    """Build a route dependency requiring explicit organization roles."""

    def dependency(
        organization_id: UUID,
        current_user: Annotated[User, Depends(get_current_user)],
        session: Annotated[Session, Depends(get_database_session)],
    ) -> Membership:
        try:
            return require_membership_role(
                session,
                organization_id=organization_id,
                user_id=current_user.id,
                allowed_roles=allowed_roles,
            )
        except OrganizationAccessError as exc:
            raise _organization_access_error() from exc

    return dependency


def _organization_access_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Organization access is not available.",
    )
