# Vault Project State

This file is the living source of truth for Vault.

Update it after every completed step.

Do not let implementation drift away from this file. If the plan changes, update this file first.

> Note: this file is a detailed build journal and project-control document.
> It is intentionally long and is not meant to be read end-to-end.
> For a quick overview, start with `README.md`.

---

## How to use this file

Keep this file in the repository at:

```text
docs/Project_State.md
```

Recommended companion files:

```text
README.md
docs/Architecture.md
docs/Step_Plan.md
docs/Project_State.md
```

Project-control rule:

> The Project State file defines what the project is allowed to become. The code proves whether it actually became that.

---

## Current status

Current step: Step 2 — FastAPI app shell.

Status: Complete with local environment limitations documented.

Approximate project completion: 8%.

Current summary:

* Vault has an initial `src/` Python package layout.
* Tooling is configured in `pyproject.toml` for pytest, Ruff, and mypy.
* Runtime dependencies now include FastAPI.
* Development dependencies now include httpx for FastAPI test-client support.
* The package exposes a simple string version constant.
* A small typed settings helper exists in `src/vault/config.py`.
* A base `VaultError` exists in `src/vault/exceptions.py`.
* A minimal FastAPI app factory exists at `src/vault/api/main.py`.
* The app is configured with the Vault title, honest description, and package
  version.
* A thin health route module exposes `GET /health`.
* `GET /health` returns `{"status": "ok", "service": "vault"}`.
* The OpenAPI schema is reachable at `/openapi.json`.
* A placeholder `api/dependencies.py` exists for later route dependencies.
* A thin CLI shell exists at `scripts/run_vault.py` and supports `--help`.
* Tests cover package import, CLI help, app creation, health response, and
  OpenAPI schema access.
* No database connections, auth, organizations, uploads, reviews, audit logs,
  exports, Docker files, CI files, sample outputs, or local databases were
  added.

Current validation status:

```text
python -m ruff check .          PASS
python -m mypy src scripts tests PASS
python -m pytest                PASS, 7 passed
python -m bandit -r src         PASS, no issues identified
python -m pip_audit             NOT COMPLETED: DNS/network failure while
                                querying pypi.org from this environment
python scripts/run_vault.py --help PASS
git status                      NOT COMPLETED: uploaded repo zip did not
                                include .git metadata in this environment
```

Required validation commands:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
git status
```

Validation rule:

> Do not mark a step complete until the required validation commands have been run locally, or until the failure is explicitly documented with the reason.

Next planned step:

```text
Step 3 — Database configuration and Docker Compose baseline.
```

---

## Project name

Working name: `Vault`.

Name status: Final unless renamed before implementation.

Repository name:

```text
vault
```

Package/app name:

```text
vault
```

---

## Project goal

Build a secure accounting document workflow web app that solves this practical problem:

> Small businesses need a controlled way to upload finance documents, validate accounting fields, detect issues, approve or reject records, preserve an audit trail, and export approved records.

The project should be polished enough for recruiters and freelance clients, rigorous enough for technical review, and structured enough that a stranger can understand the design decisions from the README, docs, tests, and code.

---

## One-sentence portfolio explanation

Vault is a FastAPI and PostgreSQL finance workflow app that handles secure document intake, role-based review, audit logging, and export so small-business accounting records can move through a controlled approval process.

Resume version:

> Built Vault, a secure accounting workflow web app with FastAPI, PostgreSQL, user authentication, role-based access control, document upload validation, approval workflows, immutable audit logging, Docker Compose, CI, and security checks.

---

## Primary audience

### Hands-on users

* Small-business owners.
* Bookkeepers.
* Staff accountants.
* Finance reviewers.
* Internal-tool clients.

These users need:

* A quickstart that works.
* Safe fake/demo data.
* Clear examples.
* Useful errors.
* Output they can understand without reading the source code.

### Career / review audience

* Recruiters.
* Technical hiring managers.
* Software engineers.
* Data analysts / domain reviewers.
* Freelance clients.

These reviewers should see:

* Clear problem framing.
* Sensible scope control.
* Maintainable structure.
* Tests that prove behavior.
* Validation in CI.
* Honest documentation.
* Real security habits.
* No fake production claims.

---

## Why this project exists

Vault is meant to show clear progression after the previous portfolio projects:

* CareerSignal showed automation, data collection, tracking, and reporting.
* LedgerLens showed transaction cleanup, categorization, duplicate detection, and exports.
* Reconcile showed accounting-domain modeling, event-style thinking, invariants, reconciliation, reporting, and stronger validation discipline.
* Vault moves the skillset online with authentication, authorization, database migrations, security checks, file-upload validation, audit logs, and organization-scoped workflows.

Vault also lays groundwork for Handled because it includes users, organizations, memberships, roles, ownership, status changes, review queues, and activity history.

---

## MVP scope

The MVP will:

1. Provide user registration.
2. Provide login and authenticated routes.
3. Store passwords as hashes only.
4. Allow users to create organizations.
5. Allow organization memberships.
6. Support owner, reviewer, and viewer roles.
7. Enforce role-based access control.
8. Enforce organization-scoped data access.
9. Support secure upload of fake finance documents.
10. Validate uploaded file type, size, extension, and safe filename handling.
11. Store document metadata.
12. Store structured document facts for fake invoices/receipts.
13. Generate accounting-control flags.
14. Detect duplicate documents using file hash and invoice attributes.
15. Support pending, approved, rejected, and needs_info statuses.
16. Require a reason for review decisions.
17. Write immutable audit entries for important state changes.
18. Export approved documents, exception reports, and audit logs to CSV.
19. Include fake/sample input.
20. Include fake/sample output.
21. Include a meaningful test suite.
22. Include a working quickstart.
23. Include CI with linting, typing, tests, and security checks.

The MVP is complete when:

* A stranger can clone the repo and follow the README.
* The main happy-path workflow works end-to-end.
* Bad inputs fail with clear errors.
* Role and organization boundary tests pass.
* Upload validation tests pass.
* Audit logging tests pass.
* Tests cover happy paths, bad inputs, and important edge cases.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit is run and findings are fixed or documented.
* pip-audit is run and findings are fixed or documented.
* CI passes.
* Sample outputs are current with implemented behavior.
* No generated private/local files are committed.

---

## Full project scope

The full project may eventually include:

1. A small server-rendered dashboard.
2. OCR for fake/sample PDFs.
3. Email notification simulation.
4. S3-compatible object storage.
5. Background jobs.
6. Vendor master file.
7. Advanced exception reporting.
8. Reconcile-compatible export format.
9. Deployment documentation.
10. Rate limiting and stronger auth hardening.

Scope rule:

> Future scope is not permission to implement everything now. Do not expand scope until the current milestone works end-to-end.

---

## Explicit non-goals for MVP

The MVP will not include:

* No real user/customer data.
* No secrets or credentials in the repo.
* No production deployment claim.
* No real bank connections.
* No payment processing.
* No Stripe.
* No real OCR.
* No AI extraction.
* No React frontend.
* No mobile app.
* No real email delivery.
* No cloud storage.
* No background jobs unless explicitly added after the core app works.
* No unrelated polish before the core workflow works.

Architecture rule:

> If a feature changes important state, it must go through the official service/workflow layer, not a route, script, or test shortcut.

---

## Hard constraints

* Use Python.
* Use FastAPI for the web API.
* Use PostgreSQL for the app database.
* Use Docker Compose for local database setup.
* Use Alembic migrations.
* Keep tests fast and offline where practical.
* Keep sample data fake and safe to commit.
* Keep generated local files out of git unless intentionally committed as fake examples.
* Keep application logic inside `src/vault/`.
* Keep routes, scripts, and dashboards thin.
* Do not let tests depend on real private accounts, cloud services, or local-only paths.
* Do not add dependencies casually.
* Do not let documentation claim behavior that does not exist.
* Do not let generated sample outputs drift away from current behavior.

Project-specific constraints:

* User passwords must never be stored or logged in plain text.
* Every organization-scoped read or write must enforce organization membership.
* Every important state-changing service must write an audit entry.
* Uploaded filenames must not be trusted as storage paths.
* Uploaded files must be fake/sample files in committed examples.

---

## Engineering principles

* README-driven development.
* Maintain this Project State file after every completed step.
* At the end of every completed build step, update the entire Project State file.
* Define official names, paths, inputs, outputs, and public functions before implementation.
* Keep application logic inside `src/vault/`.
* Keep scripts and routes thin.
* Every non-trivial function should be importable and directly testable.
* Add custom exceptions instead of broad generic error handling where useful.
* Validate bad inputs early and fail with clear messages.
* Preserve raw source data before cleaning or transforming it.
* Keep business logic separate from file I/O where practical.
* Log or print at external boundaries, not deep inside business logic.
* Use clear names that describe what things are.
* Every public function should have one job and a short docstring.
* Add tests for edge cases, not just happy paths.
* Prefer small, reviewable patches over full-file rewrites.
* Do not recreate working files blindly.
* Do not treat Git as only a save button.
* Commit clean, working milestones.
* Do not polish the README as fiction. Polish it after behavior works.

Decision rule:

> If the program makes a decision, store or display why it made that decision.

Examples:

* status plus reason
* role denial plus reason
* control flag plus explanation
* duplicate score plus explanation
* validation error plus clear message
* generated output plus command that created it

---

## Repo access and handoff workflow

Best workflow:

* Work in an environment where the assistant/coding agent can inspect the whole repo, edit files, run commands, inspect diffs, and check git status.

If full repo access is not available:

* Upload a fresh repo zip at the start of each major phase.
* For each step, upload every file that may need editing.
* Include `pyproject.toml`, affected source files, affected tests, and this Project State file.
* Paste complete validation output after local runs.
* Do not ask for patches against stale files.

Reality rule:

> The Project State file tells intent. The current repo files tell reality. Implementation decisions must use both.

Required local output after each step:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
git status
```

If one command is not applicable, document why.

---

## Code style and Ruff rules

Ruff is part of the default validation suite.

Default command:

```bash
python -m ruff check .
```

Line-length rule:

> Keep generated Python code within Ruff's configured 88-character line limit before handoff.

Pay special attention to:

* SQLAlchemy model declarations.
* Long route signatures.
* Long dependency chains.
* Long test parameter lists.
* Long dictionaries.
* Long error messages.
* CLI command examples.

Preferred wrapping style:

```python
def create_document(
    session: Session,
    *,
    organization_id: UUID,
    uploaded_by_user_id: UUID,
    original_filename: str,
) -> Document:
    ...
```

Ruff rule:

> Do not rely on Ruff cleanup as a separate step. Generate Ruff-ready code first.

---

## Type-safety and mypy rules

Mypy should be included early.

Default command:

```bash
python -m mypy src scripts tests
```

Mypy setup rule:

> Add mypy to development dependencies and CI before the project grows large.

Default development dependencies should include:

```text
pytest
ruff
mypy
bandit
pip-audit
```

Type-safety rules:

* Prefer explicit return types for public functions.
* Avoid broad `dict[str, object]` fallout where a dataclass, Pydantic model, or TypedDict is clearer.
* Cast external/database rows at boundaries, not throughout business logic.
* Avoid compatibility fallbacks that hide missing required fields.
* Keep scripts importable by adding `scripts/__init__.py` when scripts are checked by mypy.
* Do not add a mypy CI job until mypy passes locally.

---

## Security and data-safety rules

* Never commit secrets, credentials, tokens, or private data.
* Keep `.env` ignored.
* Keep `.env.example` committed.
* Keep generated local databases ignored.
* Prefer ORM query construction over raw SQL.
* Prefer parameterized SQL for values if raw SQL is necessary.
* If SQL identifiers must be dynamic, use an allowlist.
* Do not build string-interpolated SQL from user input.
* Do not add cloud dependencies unless explicitly scoped.
* Keep fake demo data obviously fake.
* Run Bandit before final completion.
* Run pip-audit before final completion.

SQL identifier rule:

> Values are parameterized. Identifiers are allowlisted. Nothing else gets interpolated.

Upload rule:

> User-provided filenames are display labels only. Stored filenames are generated by Vault.

Tenant rule:

> Organization access is denied unless membership is proven in the current request/service call.

Audit rule:

> Important state changes and security-sensitive actions create audit entries.

---

## Sample input and output rules

Sample files are part of the product surface.

Rules:

* Keep sample input fake and safe to commit.
* Keep sample output fake and safe to commit.
* Regenerate sample output whenever behavior changes.
* Review sample output diffs before committing.
* Do not commit local databases.
* Do not commit real uploaded files.

Required check after behavior affecting sample output:

```bash
python scripts/run_vault.py export-demo --output-dir examples/sample_output
git diff examples/sample_output
```

Drift rule:

> A stale sample output can make correct code look wrong. Update samples in the same step that changes their behavior.

---

## Official project structure

```text
vault/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── Project_State.md
│   ├── Architecture.md
│   └── Step_Plan.md
├── examples/
│   ├── sample_input/
│   └── sample_output/
├── scripts/
│   ├── __init__.py
│   └── run_vault.py
├── src/
│   └── vault/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   ├── dependencies.py
│       │   └── routes/
│       ├── audit/
│       ├── auth/
│       ├── controls/
│       ├── documents/
│       ├── exports/
│       ├── organizations/
│       ├── reviews/
│       ├── config.py
│       ├── database.py
│       └── exceptions.py
├── tests/
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── .python-version
└── .gitignore
```

Adjust this structure only if the project needs it. If changed, update this section before implementation.

---

## Official names and paths

Package/app name:

```text
vault
```

Main script:

```text
scripts/run_vault.py
```

Project State file:

```text
docs/Project_State.md
```

Architecture docs:

```text
docs/Architecture.md
docs/Step_Plan.md
```

Sample input folder:

```text
examples/sample_input/
```

Sample output folder:

```text
examples/sample_output/
```

Default output folder:

```text
exports/
```

Official output files:

```text
approved_documents.csv
exceptions_report.csv
audit_log.csv
```

---

## Official input format

### Fake invoice facts CSV

Input file:

```text
examples/sample_input/invoice_facts.csv
```

Required columns:

```text
vendor_name
invoice_number
invoice_date
amount_cents
currency
category
```

Optional columns:

```text
due_date
memo
```

All sample data must be fake and safe to commit.

### Fake uploaded document files

Input folder:

```text
examples/sample_input/uploads/
```

Allowed MVP file types:

```text
.csv
.txt
.pdf
```

Rules:

* Files must be fake.
* PDFs must contain no real personal or financial information.
* Stored filenames must be generated by the app.

---

## Official data model

### User

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| email | Yes | str | Unique normalized email. |
| password_hash | Yes | str | Raw password is never stored. |
| full_name | Yes | str | Human-readable display name. |
| is_active | Yes | bool | Disabled users cannot authenticate. |
| created_at | Yes | datetime | UTC timestamp. |

### Organization

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| name | Yes | str | Human-readable organization name. |
| created_by_user_id | Yes | UUID | Creator. |
| created_at | Yes | datetime | UTC timestamp. |

### Membership

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| organization_id | Yes | UUID | Organization scope. |
| user_id | Yes | UUID | Member. |
| role | Yes | str | owner, reviewer, or viewer. |
| created_at | Yes | datetime | UTC timestamp. |

### Document

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| organization_id | Yes | UUID | Tenant boundary. |
| uploaded_by_user_id | Yes | UUID | Uploader. |
| original_filename | Yes | str | Sanitized display name. |
| stored_filename | Yes | str | Generated safe filename. |
| content_type | Yes | str | Validated content type. |
| file_size_bytes | Yes | int | Validated file size. |
| sha256_hash | Yes | str | Integrity and duplicate check. |
| status | Yes | str | pending, approved, rejected, needs_info. |
| created_at | Yes | datetime | UTC timestamp. |

### DocumentFact

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| document_id | Yes | UUID | Linked document. |
| vendor_name | Yes | str | Fake vendor name. |
| invoice_number | No | str | Invoice number if present. |
| invoice_date | No | date | Invoice date if present. |
| due_date | No | date | Due date if present. |
| amount_cents | Yes | int | Integer cents. |
| currency | Yes | str | Default USD. |
| category | Yes | str | Accounting category. |
| memo | No | str | Optional note. |

### ControlFlag

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| document_id | Yes | UUID | Linked document. |
| flag_type | Yes | str | Type of control flag. |
| severity | Yes | str | info, warning, blocker. |
| reason | Yes | str | Human-readable explanation. |
| created_at | Yes | datetime | UTC timestamp. |

### ReviewDecision

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| document_id | Yes | UUID | Linked document. |
| reviewer_user_id | Yes | UUID | Reviewer. |
| decision | Yes | str | approved, rejected, needs_info. |
| reason | Yes | str | Required decision reason. |
| created_at | Yes | datetime | UTC timestamp. |

### AuditEntry

| Field | Required | Type | Notes |
| ----- | -------: | ---- | ----- |
| id | Yes | UUID | Stable internal ID. |
| organization_id | No | UUID | Organization scope, nullable for account events. |
| actor_user_id | No | UUID | Actor, nullable for system actions. |
| action | Yes | str | Short action name. |
| entity_type | Yes | str | document, organization, user, export. |
| entity_id | No | UUID | Affected entity. |
| summary | Yes | str | Human-readable summary. |
| metadata_json | Yes | dict | Structured details. |
| created_at | Yes | datetime | UTC timestamp. |

---

## Official storage/schema plan

Storage choice:

```text
PostgreSQL
```

Schema or persistence rules:

* Use SQLAlchemy models.
* Use Alembic migrations.
* Use UUID primary keys.
* Use UTC timestamps.
* Keep organization-scoped tables queryable by `organization_id`.
* Keep audit entries append-only through normal services.
* Keep uploaded files outside the source tree.
* Store file metadata in PostgreSQL.
* Store file bytes on local disk for MVP.

---

## Official output format

The MVP should generate:

```text
examples/sample_output/approved_documents.csv
examples/sample_output/exceptions_report.csv
examples/sample_output/audit_log.csv
```

Output rules:

* CSV headers must be stable.
* Rows must use fake data only.
* Amounts must export as integer cents and/or formatted decimal fields.
* Audit exports must include action, actor, entity, summary, and timestamp.
* Exception exports must include flag type, severity, reason, and document reference.

---

## Official CLI / interface behavior

The MVP should eventually support:

```bash
python scripts/run_vault.py --help
python scripts/run_vault.py seed-demo
python scripts/run_vault.py export-demo --output-dir examples/sample_output
```

API behavior:

```text
GET /health
POST /auth/register
POST /auth/login
POST /organizations
GET /organizations/{organization_id}/documents
POST /organizations/{organization_id}/documents/upload
POST /organizations/{organization_id}/documents/{document_id}/facts
POST /organizations/{organization_id}/documents/{document_id}/review
GET /organizations/{organization_id}/audit
GET /organizations/{organization_id}/exports/approved-documents
```

CLI/interface rules:

* User-facing errors should be clear.
* Core business logic should not live in the CLI wrapper.
* CLI should call package services.
* CLI should validate paths and options.
* CLI should return a non-zero exit code for failure.
* Commands should work with fake demo data.

---

## Dashboard/UI principles, if applicable

Primary UI choice:

```text
FastAPI OpenAPI docs for MVP. Optional server-rendered dashboard later.
```

UI role:

* Show the workflow clearly.
* Make outputs easy to inspect.
* Provide portfolio screenshots if useful.

UI rules:

* Keep UI logic thin.
* Do not put core business logic in UI files.
* UI should call services or query safe read models.
* UI should work with fake demo data.
* UI should not create or mutate important state unless writeback is explicitly scoped and tested.

---

## Official module responsibilities

| Module | Responsibility |
| ------ | -------------- |
| `config.py` | Store settings and environment loading. |
| `database.py` | Create engine/session helpers and database dependencies. |
| `exceptions.py` | Define custom project exceptions. |
| `api/main.py` | Create FastAPI app and include routes. |
| `api/dependencies.py` | Shared route dependencies. |
| `auth/` | Password hashing, login, tokens/sessions, current user. |
| `organizations/` | Organizations, memberships, role checks. |
| `documents/` | Upload validation, metadata, document facts. |
| `controls/` | Accounting-control flags and duplicate detection. |
| `reviews/` | Review decisions and status transitions. |
| `audit/` | Immutable audit entry creation and queries. |
| `exports/` | CSV export builders and writers. |
| `scripts/run_vault.py` | Thin local CLI helper. |

Rule:

> Modules should have one main responsibility. Do not let routes, scripts, importers, or services become junk drawers.

---

## Dependency decisions

Dependency source of truth:

```text
pyproject.toml
```

Do not create unless explicitly needed:

```text
requirements.txt
```

Planned runtime dependencies:

* `fastapi` — web API.
* `uvicorn` — local ASGI server.
* `sqlalchemy` — ORM/database layer.
* `alembic` — database migrations.
* `psycopg` — PostgreSQL driver.
* `pydantic-settings` — settings from environment.
* `python-multipart` — file upload support.
* `python-jose` or equivalent — token handling if JWT is used.
* `passlib[bcrypt]`, `pwdlib`, or equivalent — password hashing.

Planned development dependencies:

* `pytest` — test framework.
* `httpx` — FastAPI test client support if needed.
* `ruff` — linting and import checks.
* `mypy` — static typing.
* `bandit` — security static analysis.
* `pip-audit` — dependency vulnerability scan.

Possible later dependencies:

* `hypothesis` — property-based tests if useful.
* `pytest-cov` — coverage if useful.
* `jinja2` — server-rendered dashboard if added.
* `boto3` — S3 storage only if cloud storage is explicitly scoped later.

Dependency rule:

> Add a dependency only when it clearly beats a simple standard-library solution.

---

## Testing decisions

Testing framework:

```text
pytest
```

Linting tool:

```text
ruff
```

Type checker:

```text
mypy
```

Security checks:

```text
bandit
pip-audit
```

Testing targets:

* Add tests with every meaningful feature.
* Test happy paths.
* Test bad inputs.
* Test edge cases.
* Test role-based access control.
* Test organization data boundaries.
* Test upload validation.
* Test audit log creation.
* Test read-only helpers do not mutate state.
* Keep tests fast and offline where practical.
* Mock filesystem, network, time, or external boundaries where practical.
* Add a coverage floor only if the project becomes large enough to justify it.

Default commands:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
```

Later smoke-check commands:

```bash
python scripts/run_vault.py --help
python scripts/run_vault.py seed-demo
python scripts/run_vault.py export-demo --output-dir examples/sample_output
```

---

## Property-based testing plan, if applicable

Property tests may be useful for upload validation and duplicate detection.

Core invariants to test later:

1. A user cannot access data from an organization where they are not a member.
2. A viewer cannot mutate organization documents or review decisions.
3. Approved/rejected/needs_info decisions always require a reason.
4. Uploaded stored filenames are generated and never equal unsafe user-provided paths.
5. Duplicate detection returns explanations for every generated duplicate flag.

Test naming rule:

> Test names should explain the rule being protected.

Example names:

```python
def test_user_cannot_read_document_from_another_organization():
    ...


def test_viewer_cannot_approve_document():
    ...
```

---

## Git and commit rules

* Use atomic commits with clear messages.
* One completed step should usually become one commit.
* Do not commit broken tests unless there is a specific reason.
* Do not mix unrelated cleanup with feature work.
* Check `git status` before and after staging.
* Review diffs before committing.
* Do not leave generated real data in the repo.
* Do not commit local databases.
* Do not commit uploaded file storage.
* Prefer committing sample CSV/JSON outputs over binary database files.

Commit message examples:

```text
Add Vault planning docs
Add project skeleton and tooling baseline
Add FastAPI app shell
Add database configuration
Add migration baseline
Add user model and password hashing
Add registration and login
Add organizations and memberships
Add role-based authorization
Add document metadata model
Add secure document upload validation
Add structured document facts
Add accounting control checks
Add duplicate document detection
Add document review workflow
Add immutable audit logging
Add CSV exports and sample outputs
Add local demo CLI
Add CI workflow
Polish README quickstart
Add final hardening cleanup
```

---

## GitHub setup checklist

First GitHub setup tasks:

* Create a new GitHub repository named `vault`.
* Keep it public if intended as a portfolio project.
* Do not add a GitHub README if the local README already exists.
* Do not add a GitHub `.gitignore` if the local `.gitignore` will be created manually.
* Do not add a license unless the license decision is final.
* Clone the repo locally.
* Add `README.md`.
* Add `docs/Project_State.md`.
* Add `docs/Architecture.md`.
* Add `docs/Step_Plan.md`.
* Commit the planning files first.
* Push the first commit to GitHub.
* Confirm the README displays correctly on GitHub.

---

## CI workflow requirements

CI should run on:

```text
push
pull_request
```

CI should run:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
```

CI may also run:

```bash
python -m pip_audit
```

CI rules:

* Keep CI simple before adding caching or matrices.
* Do not add deployment jobs until deployment is actually in scope.
* Do not add a failing mypy job before mypy passes locally.
* Use the same commands locally and in CI.

---

## Architecture decision records

### ADR 001 — Build Vault as a FastAPI web app

Decision:

* Vault will use FastAPI rather than another local CLI/dashboard-first architecture.

Why:

* The project needs to address online workflows, authentication, authorization, APIs, and security.
* FastAPI is portfolio-friendly and testable.
* OpenAPI docs provide a usable MVP interface without a frontend detour.

Alternatives considered:

* Streamlit dashboard.
* Flask.
* Django.
* React/full-stack app from day one.

Tradeoff accepted:

* A polished frontend is deferred to keep the MVP focused on backend, auth, controls, and security.

Status:

* Accepted.

### ADR 002 — Use PostgreSQL instead of SQLite

Decision:

* Vault will use PostgreSQL for application persistence.

Why:

* The previous projects already used SQLite heavily.
* PostgreSQL better demonstrates production-style web app development.
* Migrations, constraints, and tenant-scoped querying are part of the learning goal.

Alternatives considered:

* SQLite.
* File-based storage.

Tradeoff accepted:

* Local setup is slightly heavier, so Docker Compose will be included.

Status:

* Accepted.

### ADR 003 — Use structured fake document facts before OCR

Decision:

* MVP document facts will come from structured fake sample data rather than OCR.

Why:

* The project goal is secure workflow, review, controls, audit, and export.
* OCR would add complexity before the core workflow exists.
* Structured input is easier to test and explain.

Alternatives considered:

* PDF OCR from the start.
* AI extraction from uploaded documents.

Tradeoff accepted:

* The MVP is less flashy, but more reliable and reviewable.

Status:

* Accepted.

### ADR 004 — Local file storage for MVP

Decision:

* Uploaded files will be stored on local disk for MVP.

Why:

* Cloud storage introduces credentials, costs, and deployment complexity.
* The project can still demonstrate secure filename handling, file validation, metadata storage, and hashing.

Alternatives considered:

* S3.
* Database BLOB storage.

Tradeoff accepted:

* Cloud storage is deferred to future scope.

Status:

* Accepted.

---

## Step prompt template

Use this prompt structure for every build step:

````markdown
Vault Step [Number] only.

Current status:
- Step [previous] is complete.
- We are now working on Step [Number].
- Do not assume future steps are complete.

Repo context available:
- [Full repo access / repo zip uploaded / specific files uploaded]
- Current Project State file is available.
- Current `pyproject.toml` is available if created.

Goal for this step:
[One clear outcome.]

Allowed files to create/edit:
- [file]
- [file]
- docs/Project_State.md

Do not edit:
- [file]
- [file]

Do not implement yet:
- [future feature]
- [future feature]
- [scope danger]

Requirements:
- [specific behavior]
- [specific behavior]
- [specific behavior]

Tests required:
- Add/update tests for [specific behavior].
- Include happy-path tests.
- Include bad-input or edge-case tests.
- Existing tests must still pass.

Style and type requirements:
- Keep all Python lines under Ruff's 88-character line limit.
- Break long route signatures, SQLAlchemy models, dictionaries,
  parametrized tests, and error messages before handoff.
- Keep public functions typed.
- Avoid broad `dict[str, object]` fallout when a narrower type is practical.

Security requirements, if applicable:
- Do not commit secrets.
- Keep organization boundaries enforced.
- Keep uploads fake and safe.
- Do not trust user-provided filenames.
- Add or update security-relevant tests.

Sample-output requirements, if behavior affects examples:
- Regenerate sample outputs.
- Review `git diff examples/sample_output`.
- Keep fake sample data only.

Commands to run:
```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
git status
```

Project State update:
- Update docs/Project_State.md.
- Mark this step complete.
- Add completed work.
- Add commands run.
- Add validation results.
- Add next planned step.

Definition of done:
- The requested feature works.
- New tests cover the feature.
- Relevant edge cases are tested.
- Existing tests still pass.
- Ruff passes.
- Mypy passes, if included in the project validation suite.
- Security checks pass or documented findings are explained.
- Project State is updated.
- Git status only shows expected files.
- A clean commit message is suggested.

Git guidance:
- Show expected git status.
- Recommend one atomic commit message.
````

---

## Standard project phases

Use these phases unless this file is updated first.

### Phase 0 — Planning

* README draft.
* Project State.
* MVP scope.
* Non-goals.
* Architecture plan.
* Data model plan.
* Step plan.
* Validation plan.

### Phase 1 — Foundation

* Folders.
* `pyproject.toml`.
* `.gitignore`.
* `.env.example`.
* Package import.
* First smoke test.
* pytest.
* Ruff.
* mypy.
* Bandit.
* pip-audit.
* FastAPI app shell.
* Docker Compose.
* Alembic baseline.

### Phase 2 — Users, auth, and organizations

* User model.
* Password hashing.
* Registration.
* Login.
* Auth dependency.
* Organizations.
* Memberships.
* Roles.
* Authorization tests.

### Phase 3 — Document intake

* Document metadata.
* Upload validation.
* Safe storage names.
* File hashes.
* Structured document facts.

### Phase 4 — Controls and review workflow

* Control flags.
* Duplicate detection.
* Review decisions.
* Status transitions.
* Required decision reasons.

### Phase 5 — Audit and exports

* Audit entries.
* Audit route/query.
* Approved document export.
* Exception export.
* Audit log export.
* Sample outputs.

### Phase 6 — CLI, docs, and CI

* Thin CLI helper.
* CI workflow.
* README quickstart.
* Screenshots if useful.
* Final validation.

### Phase 7 — Type safety and hardening cleanup

* Mypy cleanup.
* Security scan review.
* Dependency audit review.
* Upload safety review.
* Authorization boundary review.
* Sample-output drift review.
* Final CI confirmation.

---

## Step history

### Step 0 — Planning and Project State

Status: Drafted.

Goal:

* Define the project before implementation begins.

Completed work:

* Selected `Vault` as the project name.
* Defined Vault as a secure accounting document workflow web app.
* Drafted README.
* Drafted Architecture document.
* Drafted Step Plan.
* Drafted Project State file.
* Defined MVP scope.
* Defined explicit non-goals.
* Defined official project structure.
* Defined official input/output formats.
* Defined validation commands.
* Defined initial architecture decisions.

Allowed files to create/edit:

```text
README.md
docs/Project_State.md
docs/Architecture.md
docs/Step_Plan.md
```

Commands to run:

```bash
git status
```

Validation note:

```text
Only planning files exist so far. Full Python validation begins after Step 1 creates the project skeleton.
```

Definition of done:

* Project goal is clear.
* MVP is clear.
* Non-goals are clear.
* Official paths are clear.
* Step plan is clear.
* Validation commands are clear.
* Project State is committed.

Suggested commit message:

```text
Add Vault planning docs
```

### Step 1 — Project skeleton and tooling baseline

Status: Complete with documented environment limitations.

Goal:

* Create the initial Python package, tooling configuration, and first smoke test.

Completed work:

* Added `pyproject.toml` with `src/` package layout configuration.
* Configured the project/package name as `vault`.
* Declared development dependencies for pytest, Ruff, mypy, Bandit, and
  pip-audit.
* Configured pytest to discover tests in `tests/`.
* Configured Ruff with an 88-character line length.
* Configured mypy for strict checking against `src`, `scripts`, and `tests`.
* Added `.gitignore` for virtual environments, Python caches, test caches,
  coverage files, `.env`, local databases, local exports, uploaded files,
  and build metadata.
* Added `.env.example` with safe fake/default environment variable names.
* Added `.python-version`.
* Added minimal importable `vault` package.
* Added `src/vault/__init__.py` with a string package version constant.
* Added `src/vault/config.py` with a small typed settings helper.
* Added `src/vault/exceptions.py` with base `VaultError`.
* Added `scripts/__init__.py`.
* Added `scripts/run_vault.py` as a thin CLI shell.
* Added `tests/test_package_import.py` with package import, version,
  exception import, and CLI help smoke tests.

Files created or edited:

```text
pyproject.toml
.gitignore
.env.example
.python-version
src/vault/__init__.py
src/vault/config.py
src/vault/exceptions.py
scripts/__init__.py
scripts/run_vault.py
tests/test_package_import.py
docs/Project_State.md
```

Commands run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 6 source files.

python -m pytest
4 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
The code validation checks that can run offline all passed. The pip-audit and
git status limitations are environment issues from this uploaded zip/runtime,
not implemented project behavior.
```

Definition of done:

* Package imports.
* First smoke test passes.
* CLI help works.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* Project State is updated.

Suggested commit message:

```text
Add project skeleton and tooling baseline
```

---

### Step 2 — FastAPI app shell

Status: Complete with documented environment limitations.

Goal:

* Add a minimal FastAPI application shell with a health endpoint and tests,
  while keeping the app ready for later route modules.

Completed work:

* Added FastAPI as a runtime dependency in `pyproject.toml`.
* Added httpx as a development dependency for FastAPI test-client support.
* Added `src/vault/api/__init__.py`.
* Added `src/vault/api/main.py` with a typed `create_app()` function.
* Configured the FastAPI app with title `Vault`, package version, and an
  honest description of the current app shell.
* Added `src/vault/api/dependencies.py` as a minimal placeholder module.
* Added `src/vault/api/routes/__init__.py`.
* Added `src/vault/api/routes/health.py` with a thin health route module.
* Added a typed Pydantic `HealthResponse` model.
* Added `GET /health` returning `{"status": "ok", "service": "vault"}`.
* Confirmed `/openapi.json` is reachable through the test client.
* Added `tests/test_api_health.py` for app creation, health response, and
  OpenAPI schema tests.
* Kept the CLI shell thin and confirmed `scripts/run_vault.py --help` still
  works.
* Did not add database, authentication, organizations, uploads, reviews, audit
  logging, exports, Docker, Alembic, CI, sample outputs, or local databases.

Files created or edited:

```text
pyproject.toml
src/vault/api/__init__.py
src/vault/api/main.py
src/vault/api/dependencies.py
src/vault/api/routes/__init__.py
src/vault/api/routes/health.py
tests/test_api_health.py
docs/Project_State.md
```

Commands run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 12 source files.

python -m pytest
7 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
The code validation checks that can run offline all passed. The pip-audit and
git status limitations are environment issues from this uploaded zip/runtime,
not implemented project behavior.
```

Definition of done:

* `create_app()` exists and returns a FastAPI app.
* `GET /health` works.
* `/openapi.json` works.
* The app imports without requiring a database.
* Tests cover the app shell and health endpoint.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Project State is updated.

Suggested commit message:

```text
Add FastAPI app shell
```

---

## Portfolio readiness checklist

Before calling the project complete:

* [ ] Can the project be explained in one sentence?
* [ ] Does the README show what problem it solves?
* [ ] Does the quickstart work from a clean clone?
* [ ] Are sample inputs fake and safe?
* [ ] Are sample outputs committed if useful?
* [ ] Are sample outputs current with behavior?
* [ ] Are screenshots included if useful?
* [ ] Is the architecture documented?
* [ ] Are important design decisions documented?
* [ ] Do tests pass?
* [ ] Does Ruff pass?
* [ ] Does mypy pass?
* [ ] Does Bandit pass or are findings documented?
* [ ] Does pip-audit pass or are findings documented?
* [ ] Does CI pass on GitHub?
* [ ] Are non-goals clear?
* [ ] Is the repo structure clean?
* [ ] Is the main workflow testable?
* [ ] Do routes avoid owning business logic?
* [ ] Is auth implemented safely?
* [ ] Is organization scoping tested?
* [ ] Is upload validation tested?
* [ ] Is the audit log tested?
* [ ] Is the Project State marked complete?
* [ ] Is the final git status clean?

---

## Final completion summary

Status: Not complete.

Final project summary:

* Fill in only when complete.

Final commands run:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
git status
```

Final repository state:

```text
Not complete.
```

Known future improvements:

* Server-rendered dashboard.
* OCR for fake/sample PDFs.
* S3-compatible object storage.
* Background jobs.
* Email notification simulation.
* Reconcile-compatible export format.
