"""Smoke tests for the initial Vault package baseline."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import vault
from vault.exceptions import VaultError


def test_package_imports_successfully() -> None:
    """The Vault package can be imported."""
    assert vault is not None


def test_package_exposes_string_version() -> None:
    """The package exposes a simple string version."""
    assert isinstance(vault.__version__, str)
    assert vault.__version__


def test_vault_error_can_be_imported() -> None:
    """The base project exception can be imported and instantiated."""
    error = VaultError("example")

    assert str(error) == "example"


def test_cli_help_command_succeeds() -> None:
    """The initial CLI shell supports --help."""
    script_path = Path("scripts/run_vault.py")

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Vault local CLI helper" in result.stdout
