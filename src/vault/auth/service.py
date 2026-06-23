"""User creation and login services for Vault authentication."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.auth.passwords import hash_password, verify_password
from vault.auth.tokens import decode_access_token
from vault.exceptions import (
    AuthenticationError,
    DuplicateUserError,
    InactiveUserError,
    ValidationError,
)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Safe authenticated-user data returned by login services."""

    id: UUID
    email: str
    full_name: str
    is_active: bool


def create_user(
    session: Session,
    *,
    email: str,
    raw_password: str,
    full_name: str,
) -> User:
    """Create a user with normalized email and hashed password."""
    normalized_email = _normalize_email(email)
    clean_full_name = _require_not_blank(full_name, "full_name")
    _validate_password(raw_password)
    _ensure_email_is_available(session, normalized_email)

    user = User()
    user.email = normalized_email
    user.password_hash = hash_password(raw_password)
    user.full_name = clean_full_name
    user.is_active = True

    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise DuplicateUserError("A user with this email already exists.") from exc

    return user


def authenticate_user(
    session: Session,
    *,
    email: str,
    raw_password: str,
) -> AuthenticatedUser:
    """Return safe active-user data when credentials are valid."""
    normalized_email = _normalize_email(email)
    _validate_password(raw_password)

    user = session.scalar(select(User).where(User.email == normalized_email))
    if user is None:
        raise AuthenticationError("Invalid email or password.")

    if not verify_password(raw_password, user.password_hash):
        raise AuthenticationError("Invalid email or password.")

    if not user.is_active:
        raise InactiveUserError("Inactive users cannot log in.")

    return AuthenticatedUser(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
    )



def load_active_user_from_token(session: Session, token: str) -> User:
    """Load the active user identified by a valid access token."""
    payload = decode_access_token(token)
    try:
        user_id = UUID(payload["sub"])
    except ValueError as exc:
        raise AuthenticationError("Invalid access token.") from exc

    user = session.get(User, user_id)
    if user is None:
        raise AuthenticationError("Invalid access token.")
    if not user.is_active:
        raise InactiveUserError("Inactive users cannot authenticate.")

    return user

def _normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()
    if normalized_email == "":
        raise ValidationError("email is required.")
    return normalized_email


def _require_not_blank(value: str, field_name: str) -> str:
    clean_value = value.strip()
    if clean_value == "":
        raise ValidationError(f"{field_name} is required.")
    return clean_value


def _validate_password(raw_password: str) -> None:
    if raw_password.strip() == "":
        raise ValidationError("password is required.")


def _ensure_email_is_available(session: Session, email: str) -> None:
    existing_user_id = session.scalar(select(User.id).where(User.email == email))
    if existing_user_id is not None:
        raise DuplicateUserError("A user with this email already exists.")
