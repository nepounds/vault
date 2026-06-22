"""User creation services for Vault authentication."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from vault.auth.models import User
from vault.auth.passwords import hash_password
from vault.exceptions import DuplicateUserError, ValidationError


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
