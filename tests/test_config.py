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
