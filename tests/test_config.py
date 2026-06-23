"""Tests for Vault environment-based settings."""

from __future__ import annotations

from vault.config import VaultSettings, load_settings


def test_settings_defaults_are_safe_for_local_development() -> None:
    """Settings can be loaded without real secrets or private environment."""
    settings = load_settings({})

    assert settings == VaultSettings()
    assert settings.app_name == "Vault"
    assert settings.environment == "development"
    assert settings.database_url == "postgresql+psycopg://localhost/vault"
    assert settings.upload_dir == "var/uploads"


def test_database_url_can_be_read_from_environment() -> None:
    """The database URL can be overridden by environment variables."""
    database_url = "postgresql+psycopg://vault_local:fake@localhost/vault_test"

    settings = load_settings({"VAULT_DATABASE_URL": database_url})

    assert settings.database_url == database_url


def test_token_settings_have_safe_local_defaults() -> None:
    """Token settings can load locally without real secrets."""
    settings = load_settings({})

    assert settings.token_secret_key == "vault-local-development-secret"
    assert settings.token_algorithm == "HS256"
    assert settings.access_token_expiration_minutes == 30


def test_token_settings_can_be_read_from_environment() -> None:
    """Token settings can be overridden by environment variables."""
    settings = load_settings(
        {
            "VAULT_TOKEN_SECRET_KEY": "fake test secret",
            "VAULT_TOKEN_ALGORITHM": "HS256",
            "VAULT_ACCESS_TOKEN_EXPIRATION_MINUTES": "15",
        }
    )

    assert settings.token_secret_key == "fake test secret"
    assert settings.token_algorithm == "HS256"
    assert settings.access_token_expiration_minutes == 15
