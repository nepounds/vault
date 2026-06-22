"""Shared SQLAlchemy model metadata for Vault."""

from __future__ import annotations

from vault.auth.models import User
from vault.database import Base

__all__ = ["Base", "User"]
