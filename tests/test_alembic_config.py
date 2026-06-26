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
CREATE_USERS_NAME = "0002_create_users.py"
CREATE_ORGS_NAME = "0003_orgs_memberships.py"
CREATE_DOCUMENTS_NAME = "0004_create_documents.py"


def test_alembic_ini_exists() -> None:
    assert Path("alembic.ini").is_file()


def test_alembic_env_exists() -> None:
    assert (ALEMBIC_DIR / "env.py").is_file()


def test_alembic_versions_directory_exists() -> None:
    assert VERSIONS_DIR.is_dir()


def test_expected_revision_files_exist() -> None:
    revision_files = sorted(VERSIONS_DIR.glob("*.py"))

    assert [revision.name for revision in revision_files] == [
        BASELINE_NAME,
        CREATE_USERS_NAME,
        CREATE_ORGS_NAME,
        CREATE_DOCUMENTS_NAME,
    ]


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


def test_create_users_revision_metadata() -> None:
    create_users = _load_module(VERSIONS_DIR / CREATE_USERS_NAME)

    assert create_users.revision == "0002_create_users"
    assert create_users.down_revision == "0001_baseline"


def test_create_users_revision_creates_only_users_table() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_USERS_NAME).read_text(encoding="utf-8"),
    )
    upgrade_calls = _function_calls(tree, "upgrade")

    create_table_calls = [
        call
        for call in upgrade_calls
        if _call_name(call) == "op.create_table"
    ]
    assert len(create_table_calls) == 1
    assert _first_string_arg(create_table_calls[0]) == "users"
    assert not any(_call_name(call) == "op.drop_table" for call in upgrade_calls)


def test_create_users_revision_drops_only_users_table() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_USERS_NAME).read_text(encoding="utf-8"),
    )
    downgrade_calls = _function_calls(tree, "downgrade")

    drop_table_calls = [
        call
        for call in downgrade_calls
        if _call_name(call) == "op.drop_table"
    ]
    assert len(drop_table_calls) == 1
    assert _first_string_arg(drop_table_calls[0]) == "users"
    assert not any(_call_name(call) == "op.create_table" for call in downgrade_calls)


def test_create_organizations_revision_metadata() -> None:
    create_orgs = _load_module(VERSIONS_DIR / CREATE_ORGS_NAME)

    assert create_orgs.revision == "0003_orgs_memberships"
    assert create_orgs.down_revision == "0002_create_users"


def test_create_organizations_revision_creates_only_org_tables() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_ORGS_NAME).read_text(encoding="utf-8"),
    )
    upgrade_calls = _function_calls(tree, "upgrade")

    create_table_calls = [
        call
        for call in upgrade_calls
        if _call_name(call) == "op.create_table"
    ]
    created_tables = [_first_string_arg(call) for call in create_table_calls]

    assert created_tables == ["organizations", "memberships"]
    assert not any(_call_name(call) == "op.drop_table" for call in upgrade_calls)


def test_create_organizations_revision_drops_only_org_tables() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_ORGS_NAME).read_text(encoding="utf-8"),
    )
    downgrade_calls = _function_calls(tree, "downgrade")

    drop_table_calls = [
        call
        for call in downgrade_calls
        if _call_name(call) == "op.drop_table"
    ]
    dropped_tables = [_first_string_arg(call) for call in drop_table_calls]

    assert dropped_tables == ["memberships", "organizations"]
    assert not any(
        _call_name(call) == "op.create_table" for call in downgrade_calls
    )


def test_create_documents_revision_metadata() -> None:
    create_documents = _load_module(VERSIONS_DIR / CREATE_DOCUMENTS_NAME)

    assert create_documents.revision == "0004_create_documents"
    assert create_documents.down_revision == "0003_orgs_memberships"


def test_create_documents_revision_creates_only_documents_table() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_DOCUMENTS_NAME).read_text(encoding="utf-8"),
    )
    upgrade_calls = _function_calls(tree, "upgrade")

    create_table_calls = [
        call
        for call in upgrade_calls
        if _call_name(call) == "op.create_table"
    ]
    created_tables = [_first_string_arg(call) for call in create_table_calls]

    assert created_tables == ["documents"]
    assert not any(_call_name(call) == "op.drop_table" for call in upgrade_calls)


def test_create_documents_revision_drops_only_documents_table() -> None:
    tree = ast.parse(
        (VERSIONS_DIR / CREATE_DOCUMENTS_NAME).read_text(encoding="utf-8"),
    )
    downgrade_calls = _function_calls(tree, "downgrade")

    drop_table_calls = [
        call
        for call in downgrade_calls
        if _call_name(call) == "op.drop_table"
    ]
    dropped_tables = [_first_string_arg(call) for call in drop_table_calls]

    assert dropped_tables == ["documents"]
    assert not any(
        _call_name(call) == "op.create_table" for call in downgrade_calls
    )

def test_alembic_target_metadata_includes_current_tables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("VAULT_DATABASE_URL", raising=False)

    env = _load_module(ALEMBIC_DIR / "env.py")

    assert "users" in env.target_metadata.tables
    assert "organizations" in env.target_metadata.tables
    assert "memberships" in env.target_metadata.tables
    assert "documents" in env.target_metadata.tables


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


def _function_calls(tree: ast.Module, function_name: str) -> list[ast.Call]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return [child for child in ast.walk(node) if isinstance(child, ast.Call)]

    raise AssertionError(f"Function {function_name!r} was not found")


def _call_name(call: ast.Call) -> str | None:
    function = call.func
    if isinstance(function, ast.Attribute) and isinstance(function.value, ast.Name):
        return f"{function.value.id}.{function.attr}"
    if isinstance(function, ast.Name):
        return function.id
    return None


def _first_string_arg(call: ast.Call) -> str | None:
    first_arg = call.args[0] if call.args else None
    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
        return first_arg.value
    return None
