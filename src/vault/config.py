"""Configuration helpers for Vault."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VaultSettings:
    """Runtime settings loaded from environment variables."""

    app_name: str = "Vault"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://localhost/vault"
    upload_dir: str = "var/uploads"


def load_settings(environ: Mapping[str, str] | None = None) -> VaultSettings:
    """Load Vault settings from environment variables."""
    source = os.environ if environ is None else environ
    return VaultSettings(
        app_name=source.get("VAULT_APP_NAME", "Vault"),
        environment=source.get("VAULT_ENVIRONMENT", "development"),
        database_url=source.get(
            "VAULT_DATABASE_URL",
            "postgresql+psycopg://localhost/vault",
        ),
        upload_dir=source.get("VAULT_UPLOAD_DIR", "var/uploads"),
    )
