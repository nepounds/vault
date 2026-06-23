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
    token_secret_key: str = "vault-local-development-secret"
    token_algorithm: str = "HS256"
    access_token_expiration_minutes: int = 30


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
        token_secret_key=source.get(
            "VAULT_TOKEN_SECRET_KEY",
            "vault-local-development-secret",
        ),
        token_algorithm=source.get("VAULT_TOKEN_ALGORITHM", "HS256"),
        access_token_expiration_minutes=int(
            source.get("VAULT_ACCESS_TOKEN_EXPIRATION_MINUTES", "30")
        ),
    )
