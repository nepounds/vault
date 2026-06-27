"""Tests for the deterministic local demo export CLI command."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.run_vault import export_demo
from vault.exports.builders import (
    APPROVED_DOCUMENTS_HEADERS,
    AUDIT_LOG_HEADERS,
    EXCEPTIONS_REPORT_HEADERS,
)

OFFICIAL_EXPORT_FILENAMES = {
    "approved_documents.csv",
    "exceptions_report.csv",
    "audit_log.csv",
}
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_vault.py"
SAMPLE_INPUT_PATH = REPO_ROOT / "examples" / "sample_input"
SAMPLE_OUTPUT_PATH = REPO_ROOT / "examples" / "sample_output"
RISKY_OUTPUT_TEXT = (
    "password",
    "password_hash",
    "bearer ",
    "access_token",
    "token_payload",
    "eyj",
    "c:\\\\",
    "/users/",
    "/home/",
)
RISKY_SAMPLE_TEXT = (
    "ssn",
    "social security",
    "tax id",
    "routing number",
    "account number",
    "bearer ",
    "access_token",
    "password",
    "secret",
)


def run_cli(
    *args: str,
    output_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("VAULT_DATABASE_URL", None)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    command = [sys.executable, str(SCRIPT_PATH), *args]
    if output_dir is not None:
        command.extend(["--output-dir", str(output_dir)])

    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def read_export_files(output_dir: Path) -> dict[str, str]:
    return {
        filename: (output_dir / filename).read_text(encoding="utf-8")
        for filename in sorted(OFFICIAL_EXPORT_FILENAMES)
    }


def csv_records(csv_text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(csv_text.splitlines()))


def test_cli_help_still_works() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "export-demo" in result.stdout


def test_export_demo_cli_exits_successfully(tmp_path: Path) -> None:
    result = run_cli("export-demo", output_dir=tmp_path / "exports")

    assert result.returncode == 0
    assert "Demo exports written:" in result.stdout


def test_export_demo_creates_missing_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "missing" / "demo-output"

    written_files = export_demo(output_dir)

    assert output_dir.is_dir()
    assert {path.name for path in written_files} == OFFICIAL_EXPORT_FILENAMES
    assert set(path.name for path in output_dir.iterdir()) == OFFICIAL_EXPORT_FILENAMES


def test_export_demo_writes_exact_official_files_only(tmp_path: Path) -> None:
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    unrelated_file = output_dir / "keep-me.txt"
    unrelated_file.write_text("do not delete me", encoding="utf-8")

    export_demo(output_dir)

    assert unrelated_file.read_text(encoding="utf-8") == "do not delete me"
    assert {path.name for path in output_dir.iterdir()} == {
        *OFFICIAL_EXPORT_FILENAMES,
        "keep-me.txt",
    }
    assert not list(output_dir.glob("*.db"))
    assert not list(output_dir.glob("*.sqlite"))
    assert not (output_dir / "uploads").exists()
    assert not (output_dir / "var" / "uploads").exists()


def test_export_demo_does_not_require_database_or_external_services(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VAULT_DATABASE_URL", "postgresql+psycopg://bad/bad")
    monkeypatch.setenv("DOCKER_HOST", "tcp://127.0.0.1:1")

    written_files = export_demo(tmp_path / "exports")

    assert {path.name for path in written_files} == OFFICIAL_EXPORT_FILENAMES


def test_export_demo_is_deterministic_across_repeated_runs(tmp_path: Path) -> None:
    output_dir = tmp_path / "exports"

    export_demo(output_dir)
    first_output = read_export_files(output_dir)
    export_demo(output_dir)
    second_output = read_export_files(output_dir)

    assert first_output == second_output


def test_export_demo_overwrites_official_files_deterministically(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    for filename in OFFICIAL_EXPORT_FILENAMES:
        (output_dir / filename).write_text("stale\n", encoding="utf-8")

    export_demo(output_dir)

    for filename, contents in read_export_files(output_dir).items():
        assert contents != "stale\n", filename
        assert contents == (SAMPLE_OUTPUT_PATH / filename).read_text(encoding="utf-8")


def test_demo_export_output_has_current_stable_headers(tmp_path: Path) -> None:
    output_dir = tmp_path / "exports"
    export_demo(output_dir)

    assert (output_dir / "approved_documents.csv").read_text(
        encoding="utf-8",
    ).splitlines()[0] == ",".join(APPROVED_DOCUMENTS_HEADERS)
    assert (output_dir / "exceptions_report.csv").read_text(
        encoding="utf-8",
    ).splitlines()[0] == ",".join(EXCEPTIONS_REPORT_HEADERS)
    assert (output_dir / "audit_log.csv").read_text(
        encoding="utf-8",
    ).splitlines()[0] == ",".join(AUDIT_LOG_HEADERS)


def test_demo_export_output_includes_representative_fake_rows(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "exports"
    export_demo(output_dir)

    approved_rows = csv_records(
        (output_dir / "approved_documents.csv").read_text(encoding="utf-8"),
    )
    exception_rows = csv_records(
        (output_dir / "exceptions_report.csv").read_text(encoding="utf-8"),
    )
    audit_rows = csv_records(
        (output_dir / "audit_log.csv").read_text(encoding="utf-8"),
    )

    assert any(
        row["vendor_name"] == "Acme Demo Office Supplies"
        for row in approved_rows
    )
    assert any(row["vendor_name"] == "" for row in approved_rows)
    assert any(row["severity"] == "blocker" for row in exception_rows)
    assert any(row["severity"] == "warning" for row in exception_rows)
    assert any(row["action"] == "export_generated" for row in audit_rows)
    assert any(row["action"] == "document_uploaded" for row in audit_rows)


def test_demo_export_output_contains_no_risky_values(tmp_path: Path) -> None:
    output_dir = tmp_path / "exports"
    export_demo(output_dir)
    output_text = "\n".join(read_export_files(output_dir).values()).lower()

    for risky_text in RISKY_OUTPUT_TEXT:
        assert risky_text not in output_text


def test_committed_sample_outputs_match_regenerated_demo_output(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "exports"
    export_demo(output_dir)

    for filename, generated_text in read_export_files(output_dir).items():
        committed_text = (SAMPLE_OUTPUT_PATH / filename).read_text(encoding="utf-8")
        assert generated_text == committed_text


def test_invoice_facts_sample_exists_with_official_columns() -> None:
    sample_file = SAMPLE_INPUT_PATH / "invoice_facts.csv"

    with sample_file.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == [
        "vendor_name",
        "invoice_number",
        "invoice_date",
        "amount_cents",
        "currency",
        "category",
        "due_date",
        "memo",
    ]
    assert rows
    assert all("Demo" in row["vendor_name"] for row in rows)


def test_fake_upload_files_exist_and_use_allowed_extensions() -> None:
    upload_dir = SAMPLE_INPUT_PATH / "uploads"
    upload_files = sorted(upload_dir.iterdir())

    assert {path.name for path in upload_files} == {
        "acme-office-supplies.txt",
        "brightline-consulting.txt",
        "coastal-utilities.txt",
    }
    assert all(path.suffix == ".txt" for path in upload_files)
    assert all(path.is_file() for path in upload_files)


def test_fake_sample_input_files_do_not_contain_obvious_private_data() -> None:
    sample_files = [SAMPLE_INPUT_PATH / "invoice_facts.csv"]
    sample_files.extend(sorted((SAMPLE_INPUT_PATH / "uploads").iterdir()))
    sample_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sample_files
    ).lower()

    for risky_text in RISKY_SAMPLE_TEXT:
        assert risky_text not in sample_text
