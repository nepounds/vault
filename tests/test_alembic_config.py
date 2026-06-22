"""Tests for Vault's Alembic baseline configuration."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ALEMBIC_DIR = Path("alembic")
VERSIONS_DIR = ALEMBIC_DIR / "versions"
BASELINE_NAME = "0001_baseline.py"


def test_alembic_ini_exists() -> None:
    assert Path("alembic.ini").is_file()


def test_alembic_env_exists() -> None:
    assert (ALEMBIC_DIR / "env.py").is_file()


def test_alembic_versions_directory_exists() -> None:
    assert VERSIONS_DIR.is_dir()


def test_exactly_one_baseline_revision_exists() -> None:
    revision_files = sorted(VERSIONS_DIR.glob("*.py"))

    assert [revision.name for revision in revision_files] == [BASELINE_NAME]


def test_baseline_revision_metadata() -> None:
    baseline = _load_module(VERSIONS_DIR / BASELINE_NAME)

    assert baseline.revision == "0001_baseline"
    assert baseline.down_revision is None


def test_baseline_revision_upgrade_and_downgrade_are_empty() -> None:
    baseline = _load_module(VERSIONS_DIR / BASELINE_NAME)

    assert baseline.upgrade() is None
    assert baseline.downgrade() is None
    assert _function_body_is_only_pass(VERSIONS_DIR / BASELINE_NAME, "upgrade")
    assert _function_body_is_only_pass(VERSIONS_DIR / BASELINE_NAME, "downgrade")


def test_alembic_env_import_does_not_require_database_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VAULT_DATABASE_URL", raising=False)

    env = _load_module(ALEMBIC_DIR / "env.py")

    assert env.get_database_url() == "postgresql+psycopg://localhost/vault"
    assert env.target_metadata is not None


def test_alembic_env_connects_only_inside_online_migration_runner() -> None:
    env_source = (ALEMBIC_DIR / "env.py").read_text(encoding="utf-8")

    assert "from vault.config import load_settings" in env_source
    assert "load_settings().database_url" in env_source
    assert "connectable.connect()" in env_source
    assert env_source.index("connectable.connect()") > env_source.index(
        "def run_migrations_online",
    )


def _load_module(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load module from {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _function_body_is_only_pass(path: Path, function_name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            body = [item for item in node.body if not isinstance(item, ast.Expr)]
            return len(body) == 1 and isinstance(body[0], ast.Pass)

    raise AssertionError(f"Function {function_name!r} was not found in {path}")
