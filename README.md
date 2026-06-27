# Vault

Vault is a secure accounting document workflow API for small-business finance teams.

It handles fake finance-document intake, organization-scoped review, accounting-control flags, audit logging, and CSV export. It is a portfolio MVP, not production software.

## Problem

Small businesses often move invoices and receipts through email threads, shared folders, spreadsheets, and memory. That makes it hard to prove who uploaded a document, what was checked, who approved it, why it was rejected, and what data is ready to export.

Vault demonstrates a controlled version of that workflow using fake sample data.

## Implemented MVP features

- User registration, login, password hashing, bearer access tokens, and `GET /auth/me`.
- Organization creation with owner membership.
- Organization-scoped role checks for owner, reviewer, and viewer roles.
- Safe document upload validation for fake `.csv`, `.txt`, and `.pdf` uploads.
- Document metadata storage with generated stored filenames and SHA-256 hashes.
- Structured document facts for fake invoice/receipt data.
- Accounting-control flags for missing fields, non-USD currency, high amounts, and duplicates.
- Review decisions that move documents to `approved`, `rejected`, or `needs_info`.
- Safe audit entries for important state-changing workflows.
- Organization-scoped audit list/detail API routes.
- Organization-scoped CSV export API routes for approved documents, exception reports, and audit logs.
- Deterministic fake sample input/output files and a local demo export command.
- Tests for auth, RBAC, uploads, facts, flags, reviews, audit entries, exports, and the CLI.

## Tech stack

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL through `psycopg`
- Argon2 password hashing through `argon2-cffi`
- pytest
- Ruff
- mypy
- Bandit
- pip-audit
- Docker Compose for local PostgreSQL only
- GitHub Actions CI

## Quickstart

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
copy .env.example .env
```

Run the validation suite:

```powershell
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit --skip-editable
```

`pip-audit --skip-editable` audits third-party dependencies while skipping the local editable `vault` package, which is expected for this portfolio app.

Run the local fake export demo:

```powershell
python scripts/run_vault.py export-demo --output-dir examples/sample_output
```

Show CLI help:

```powershell
python scripts/run_vault.py --help
```

Inspect Alembic migration history:

```powershell
python -m alembic history
```

## Local PostgreSQL setup

Most tests and the demo export command do not require Docker or PostgreSQL. The API is written for PostgreSQL-backed app persistence, and Docker Compose is included for local database work.

Start local PostgreSQL:

```powershell
docker compose up -d db
```

Set the local Docker database URL, then apply migrations:

```powershell
$env:VAULT_DATABASE_URL = "postgresql+psycopg://vault_local:vault_local@localhost:5432/vault_local"
python -m alembic upgrade head
python -m alembic current
```

Stop local PostgreSQL and clear the temporary environment variable:

```powershell
docker compose down
Remove-Item Env:VAULT_DATABASE_URL
```

The `.env.example` file contains fake local defaults. Do not commit a real `.env` file.

## Demo sample data

Sample input lives under:

```text
examples/sample_input/
```

Sample output lives under:

```text
examples/sample_output/
```

The committed sample data is fake. It is meant to show expected CSV shapes without using real customers, real vendors, real invoices, private uploads, local database files, secrets, bearer tokens, password hashes, or local absolute paths.

Regenerate the sample outputs with:

```powershell
python scripts/run_vault.py export-demo --output-dir examples/sample_output
```

The command writes:

```text
examples/sample_output/approved_documents.csv
examples/sample_output/exceptions_report.csv
examples/sample_output/audit_log.csv
```

## API overview

The app exposes FastAPI routes for the implemented backend workflow:

```text
GET  /health
POST /auth/register
POST /auth/login
GET  /auth/me
POST /organizations
GET  /organizations/{organization_id}
POST /organizations/{organization_id}/documents/upload
GET  /organizations/{organization_id}/documents
GET  /organizations/{organization_id}/documents/{document_id}
POST /organizations/{organization_id}/documents/{document_id}/facts
GET  /organizations/{organization_id}/documents/{document_id}/facts
GET  /organizations/{organization_id}/documents/{document_id}/facts/{fact_id}
POST /organizations/{organization_id}/documents/{document_id}/control-flags/generate
GET  /organizations/{organization_id}/documents/{document_id}/control-flags
GET  /organizations/{organization_id}/documents/{document_id}/control-flags/{flag_id}
POST /organizations/{organization_id}/documents/{document_id}/duplicates/generate
POST /organizations/{organization_id}/documents/{document_id}/review
GET  /organizations/{organization_id}/documents/{document_id}/reviews
GET  /organizations/{organization_id}/documents/{document_id}/reviews/{review_decision_id}
GET  /organizations/{organization_id}/audit
GET  /organizations/{organization_id}/audit/{audit_entry_id}
GET  /organizations/{organization_id}/exports/approved-documents
GET  /organizations/{organization_id}/exports/exceptions-report
GET  /organizations/{organization_id}/exports/audit-log
```

FastAPI OpenAPI docs are available when the app is running at:

```text
/docs
```

## Security notes

- Passwords are stored as Argon2 hashes only.
- Bearer tokens are not included in sample output.
- Organization-scoped routes require authenticated membership.
- Owner/reviewer/viewer checks are explicit per route.
- Uploaded display filenames are not trusted as storage paths.
- Stored filenames are generated by Vault.
- Upload validation checks extension, content type, filename shape, and file size.
- Audit metadata is redacted before safe API/export responses where needed.
- `.env` is ignored; `.env.example` is fake.
- CI runs Ruff, mypy, pytest, Bandit, and `pip-audit --skip-editable`.

## Project status

MVP backend: complete after local validation.

Local pytest validation passed with one upstream FastAPI/Starlette TestClient deprecation warning. That warning is not a Vault behavior failure.

GitHub Actions CI workflow has been added. A local validation pass proves the repository state; a GitHub Actions run must still be observed in the repository UI before claiming CI is green.

## Honest limitations and non-goals

Vault does not currently include:

- production deployment,
- production-grade auth hardening,
- refresh tokens,
- password reset,
- email verification,
- member invitation or membership management routes,
- document download routes,
- OCR,
- AI extraction,
- real bank integrations,
- real customer data,
- real cloud storage,
- payment processing,
- frontend/dashboard UI,
- background jobs,
- or real email delivery.

The project is intentionally scoped as a backend portfolio MVP.
