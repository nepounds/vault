"""Password hashing helpers for Vault authentication."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

_PASSWORD_HASHER = PasswordHasher()


def hash_password(raw_password: str) -> str:
    """Return a secure password hash for a raw password."""
    return _PASSWORD_HASHER.hash(raw_password)


def verify_password(raw_password: str, password_hash: str) -> bool:
    """Return whether a raw password matches a stored password hash."""
    try:
        return _PASSWORD_HASHER.verify(password_hash, raw_password)
    except VerificationError:
        return False
