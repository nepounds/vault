from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_ci_workflow_runs_required_validation_commands() -> None:
    workflow = _read(".github/workflows/ci.yml")

    assert "on:" in workflow
    assert "push:" in workflow
    assert "pull_request:" in workflow
    assert 'python-version: "3.13"' in workflow
    assert 'python -m pip install -e ".[dev]"' in workflow
    assert "python -m ruff check ." in workflow
    assert "python -m mypy src scripts tests" in workflow
    assert "python -m pytest" in workflow
    assert "python -m bandit -r src" in workflow
    assert "python -m pip_audit" in workflow
    assert "docker compose" not in workflow.lower()


def test_readme_documents_current_mvp_without_unimplemented_claims() -> None:
    readme = _read("README.md")

    required_text = [
        "Vault is a secure accounting document workflow API",
        "Implemented MVP features",
        "Organization-scoped role checks",
        "Safe document upload validation",
        "Review decisions",
        "Safe audit entries",
        "CSV export API routes",
        "python scripts/run_vault.py export-demo --output-dir examples/sample_output",
        "python -m ruff check .",
        "python -m mypy src scripts tests",
        "python -m pytest",
        "python -m bandit -r src",
        "python -m pip_audit",
        "Most tests and the demo export command do not require Docker",
        "The committed sample data is fake",
        "MVP backend: complete after local validation",
        "Honest limitations and non-goals",
    ]
    for text in required_text:
        assert text in readme

    stale_or_unsafe_claims = [
        "Status: Planning only",
        "live OCR",
        "AI extraction is implemented",
        "production ready",
        "real bank integrations are implemented",
    ]
    for text in stale_or_unsafe_claims:
        assert text not in readme


def test_final_docs_are_not_materially_stale() -> None:
    architecture = _read("docs/Architecture.md")
    step_plan = _read("docs/Step_Plan.md")

    assert "Current implementation" in architecture
    assert "CSV export builders and authenticated export API routes" in architecture
    assert "CI runs the same core validation commands" in architecture
    assert "Step 39 is the final MVP polish step" in step_plan
    assert "Post-MVP backlog" in step_plan
    assert "Status: Planning only" not in architecture
    assert "Status: Planning only" not in step_plan
