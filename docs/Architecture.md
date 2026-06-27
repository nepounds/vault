# Vault Architecture

Vault is a FastAPI backend for a secure accounting document workflow MVP.

The main rule is boring on purpose: keep routes thin, keep business rules in importable services, keep organization boundaries explicit, and record important state changes in audit entries.

## Current implementation

Vault currently implements:

- user registration, login, bearer tokens, and current-user lookup;
- organizations, memberships, and owner/reviewer/viewer roles;
- organization-scoped document upload, listing, and detail reads;
- structured document facts for fake invoices/receipts;
- accounting-control flags and duplicate detection;
- review decisions and document status transitions;
- audit entry creation plus organization-scoped audit reads;
- CSV export builders and authenticated export API routes;
- deterministic fake sample input/output data and a local demo export command;
- GitHub Actions CI for linting, typing, tests, and security checks.

## Layering

```text
HTTP route
  -> request schema
  -> authentication dependency
  -> organization role dependency
  -> service/helper function
  -> database transaction
  -> audit entry for important state changes
  -> response schema
```

Routes should parse inputs, call services, commit or roll back a request, and return safe responses. They should not become junk drawers for business rules.

## Main modules

```text
src/vault/
├── api/              FastAPI app, routes, dependencies
├── auth/             password hashing, tokens, user services, schemas
├── organizations/    organization creation, memberships, role checks
├── documents/        upload validation, storage, metadata, facts
├── controls/         accounting-control flags and duplicate detection
├── reviews/          review decisions and status transitions
├── audit/            audit entry models, services, schemas, redaction
├── exports/          CSV row schemas, builders, database row helpers
├── config.py         safe local settings
├── database.py       SQLAlchemy base, engine, and session helpers
└── exceptions.py     custom project exceptions
```

## Persistence

Vault uses SQLAlchemy models and Alembic migrations. The app is designed for PostgreSQL, with Docker Compose included for local PostgreSQL work. Tests use isolated local database setup where practical and do not require Docker.

The current tables are:

- `users`
- `organizations`
- `memberships`
- `documents`
- `document_facts`
- `control_flags`
- `review_decisions`
- `audit_entries`

## Authorization model

Vault is multi-organization. Organization-scoped routes must prove membership before returning or changing data.

Current role behavior:

| Role | Upload | Create facts | Generate flags | Review | Export | Read audit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| owner | yes | yes | yes | yes | yes | yes |
| reviewer | yes | yes | yes | yes | yes | yes |
| viewer | no | no | no | no | no | yes |

There are no membership-management routes in the MVP.

## Upload and storage design

Uploaded filenames are display labels only. Vault validates file metadata, generates stored filenames, stores bytes under the configured upload directory, and stores document metadata in the database.

Allowed MVP file extensions are:

```text
.csv
.txt
.pdf
```

The committed examples use fake text files and fake invoice facts. The demo export command does not read real uploads.

## Audit design

Important state-changing API workflows create safe audit entries in the same request session before commit. Audit metadata avoids raw passwords, password hashes, bearer tokens, token payloads, and local absolute stored paths.

Read-only audit routes do not create audit entries.

## Export design

Export builders return CSV text from in-memory buffers. API export routes return downloadable CSV responses and write `export_generated` audit entries for successful exports.

Implemented export files:

```text
approved_documents.csv
exceptions_report.csv
audit_log.csv
```

The local demo command writes deterministic fake sample outputs:

```text
python scripts/run_vault.py export-demo --output-dir examples/sample_output
```

## Validation strategy

Required checks:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
```

Additional smoke checks:

```bash
python scripts/run_vault.py --help
python scripts/run_vault.py export-demo --output-dir examples/sample_output
python -m alembic history
```

CI runs the same core validation commands. GitHub Actions must be observed green before saying CI is green.

## Accepted MVP tradeoffs

- FastAPI OpenAPI docs are the MVP interface; no frontend is included.
- Structured fake facts are used instead of OCR or AI extraction.
- Local file storage is used instead of cloud object storage.
- Docker Compose is for local PostgreSQL only, not deployment.
- Sample output is committed as fake deterministic documentation, not customer data.
