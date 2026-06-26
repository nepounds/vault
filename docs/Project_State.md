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

Current step: Step 16 — Document metadata service.

Status: Complete with documented environment limitations.

Approximate project completion: 58%.

Current summary:

* Vault has an initial `src/` Python package layout.
* Tooling is configured in `pyproject.toml` for pytest, Ruff, and mypy.
* Runtime dependencies include FastAPI, SQLAlchemy, psycopg, Alembic, and
  argon2-cffi.
* Development dependencies include httpx for FastAPI test-client support.
* The package exposes a simple string version constant.
* A typed settings helper exists in `src/vault/config.py`.
* Settings include app name, environment, database URL, upload directory, token
  secret key, token algorithm, and access-token expiration minutes.
* Settings have safe local defaults and do not require real secrets to import.
* Token defaults are local-development/test defaults only and are not production
  secrets.
* Custom Vault exceptions exist for base project errors, validation failures,
  duplicate user creation attempts, authentication failures, inactive-user
  authentication attempts, organization validation failures, and document
  metadata validation failures.
* A minimal FastAPI app factory exists at `src/vault/api/main.py`.
* The app is configured with the Vault title, honest description, and package
  version.
* A thin health route module exposes `GET /health`.
* `GET /health` returns `{"status": "ok", "service": "vault"}`.
* The OpenAPI schema is reachable at `/openapi.json`.
* `POST /auth/register` exists and returns HTTP 201 on successful user
  registration.
* `POST /auth/login` exists and returns HTTP 200 on successful authentication.
* Successful login returns a bearer access token.
* Invalid email/password login attempts return HTTP 401 with a safe public error.
* Inactive-user login attempts return HTTP 403 with a safe public error.
* `GET /auth/me` exists and returns HTTP 200 for an authenticated active user.
* `GET /auth/me` returns safe current-user fields only: `id`, `email`,
  `full_name`, `is_active`, and `created_at`.
* `GET /auth/me` does not return raw passwords or password hashes.
* The auth route is included through the existing auth router in the FastAPI app
  factory.
* `POST /organizations` exists and returns HTTP 201 on successful authenticated
  organization creation.
* `POST /organizations` requires a valid bearer token for an active user.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens are
  rejected before organization creation.
* `POST /organizations` depends on the existing current-user dependency.
* `POST /organizations` depends on the existing database session dependency.
* The organization creation route calls the existing `create_organization()`
  service.
* The organization creation route does not manually create `Organization` or
  `Membership` ORM records.
* The organization creation route commits successful organization creation.
* The organization creation route refreshes the created organization and owner
  membership before returning.
* Organization creation requests include `name`.
* Blank and whitespace-only organization names are rejected as client errors.
* Organization creation responses return safe organization data: `id`, `name`,
  `created_by_user_id`, and `created_at`.
* Organization creation responses include owner membership data:
  `membership_id` and `role`.
* Organization creation responses do not return raw passwords, password hashes,
  token internals, or unrelated user data.
* `POST /organizations` appears in the OpenAPI schema.
* `src/vault/api/dependencies.py` provides a database session dependency that
  yields and safely closes a SQLAlchemy session.
* The database session dependency creates no global database connection at
  import time and can be overridden by route tests.
* `src/vault/api/dependencies.py` provides a reusable current-user dependency.
* The current-user dependency uses FastAPI HTTP bearer security utilities.
* The current-user dependency rejects missing, malformed, invalid, expired,
  unknown-user, and inactive-user bearer tokens with a safe public HTTP 401
  error.
* `src/vault/auth/service.py` includes a small token-to-active-user lookup
  helper for dependency use.
* A thin CLI shell exists at `scripts/run_vault.py` and supports `--help`.
* `src/vault/database.py` contains small typed SQLAlchemy helpers for creating
  an engine and session factory without connecting at import time.
* `.env.example` contains safe fake local database and upload settings.
* `docker-compose.yml` defines a local-only PostgreSQL service with a named
  volume for database data.
* Alembic migration infrastructure exists at the repository root.
* `alembic.ini`, `alembic/env.py`, `alembic/script.py.mako`, and
  `alembic/versions/` exist.
* One empty baseline migration exists at
  `alembic/versions/0001_baseline.py`.
* A shared SQLAlchemy model metadata import exists at `src/vault/models.py`.
* The shared SQLAlchemy declarative base remains in `src/vault/database.py` and
  is re-exported through `src/vault/models.py` with imported models.
* `src/vault/auth/models.py` defines the initial `User` ORM model.
* The `User` model includes `id`, `email`, `password_hash`, `full_name`,
  `is_active`, and `created_at`.
* User IDs use UUID primary keys.
* `created_at` uses a UTC-aware application-side timestamp default.
* User email is non-null and unique.
* `src/vault/auth/passwords.py` provides typed password hashing and password
  verification helpers.
* Password hashing uses Argon2 through `argon2-cffi`.
* `src/vault/auth/service.py` provides typed user creation, login, and
  token-based active-user loading services.
* The user creation service accepts a SQLAlchemy `Session`, email, raw password,
  and full name.
* User creation trims and lowercases emails before storage.
* User creation rejects blank email, blank password, and blank full-name values.
* User creation stores password hashes only, never raw passwords.
* The login service accepts a SQLAlchemy `Session`, email, and raw password.
* The login service normalizes the email before lookup.
* The login service verifies passwords through password helper functions.
* The login service rejects invalid credentials without distinguishing unknown
  email from wrong password.
* The login service rejects inactive users.
* The login service returns safe authenticated-user data and does not expose raw
  passwords or password hashes.
* `src/vault/auth/tokens.py` provides an isolated minimal JWT-style access-token
  foundation using the standard library.
* Access tokens are signed with HS256, include the user ID as `sub`, and include
  an `exp` expiration claim.
* Token decoding validates structure, signature, algorithm, token type, subject,
  and expiration.
* `src/vault/auth/schemas.py` defines explicit registration, login, and
  current-user response schemas.
* Login requests include `email` and `password`.
* Login responses include only `access_token` and `token_type`.
* Login responses do not include raw passwords or password hashes.
* Blank login request fields are rejected as client validation errors.
* Registration behavior from Step 7 remains intact.
* `src/vault/organizations/roles.py` defines the official membership roles:
  `owner`, `reviewer`, and `viewer`.
* `src/vault/organizations/models.py` defines the initial `Organization` ORM
  model.
* The `Organization` model includes `id`, `name`, `created_by_user_id`, and
  `created_at`.
* `src/vault/organizations/models.py` defines the initial `Membership` ORM
  model.
* The `Membership` model includes `id`, `organization_id`, `user_id`, `role`,
  and `created_at`.
* Organization and membership IDs use UUID primary keys.
* Organization and membership timestamps use the same UTC-aware application-side
  timestamp default as the user model.
* Organizations are connected to their creator through a foreign key to
  `users.id`.
* Memberships are connected to organizations and users through foreign keys.
* Membership metadata prevents the same user from having duplicate memberships
  in the same organization.
* Membership role metadata includes a check constraint for `owner`, `reviewer`,
  and `viewer`.
* Membership lookup indexes exist for organization and user lookup.
* Alembic `target_metadata` points at Vault model metadata that includes the
  `users`, `organizations`, and `memberships` tables.
* A create-users migration exists at
  `alembic/versions/0002_create_users.py`.
* A create-organizations-and-memberships migration exists at
  `alembic/versions/0003_orgs_memberships.py`.
* `src/vault/organizations/service.py` provides typed organization creation
  service behavior.
* The organization creation service accepts a SQLAlchemy `Session`, a creator
  `User` ORM object, and an organization name.
* Organization creation trims surrounding whitespace from organization names.
* Blank and whitespace-only organization names are rejected.
* Inactive creator users are rejected.
* Organization creation creates an `Organization` record with
  `created_by_user_id` set to the creator user's ID.
* Organization creation creates one owner `Membership` record for the creator.
* The creator membership uses the official `owner` role value.
* Organization and owner membership records are added to the same supplied
  session and flushed together so generated IDs are available.
* Organization creation does not commit automatically.
* `src/vault/organizations/service.py` provides typed organization membership
  access helpers.
* `get_membership_for_user()` returns a user's membership for an organization
  or `None` when no membership exists.
* `require_membership()` returns a user's membership or raises a safe custom
  access exception when membership is missing.
* `membership_has_role()` checks whether a membership role is explicitly
  included in the allowed role set.
* `require_membership_role()` requires organization membership and an
  explicitly allowed role.
* Organization access exceptions now include `OrganizationAccessError`,
  `OrganizationMembershipRequiredError`, and `OrganizationRoleRequiredError`.
* Organization role checks use official role values from
  `src/vault/organizations/roles.py`.
* Owner is not treated as all-powerful yet; owner, reviewer, and viewer roles
  are allowed only when explicitly included.
* Unknown role values fail closed.
* `src/vault/api/dependencies.py` provides a reusable
  `require_organization_roles()` route dependency factory.
* The organization RBAC dependency combines the current authenticated user,
  database session, `organization_id` path parameter, and explicit allowed
  role set.
* The organization RBAC dependency returns the matching `Membership` when
  access is allowed.
* Organization RBAC dependency failures return HTTP 403 with a safe generic
  public message for authenticated users who lack access.
* Unknown organizations and non-members are rejected the same way.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens still
  return the existing HTTP 401 authentication error before organization RBAC.
* `GET /organizations/{organization_id}` exists as a thin protected
  organization-detail route.
* `GET /organizations/{organization_id}` requires organization membership using
  the new reusable RBAC dependency.
* `GET /organizations/{organization_id}` returns safe organization data only:
  `id`, `name`, `created_by_user_id`, and `created_at`.
* `GET /organizations/{organization_id}` does not list members, expose unrelated
  users, or implement update/delete behavior.
* `src/vault/documents/statuses.py` defines the official document status
  values: `pending`, `approved`, `rejected`, and `needs_info`.
* `src/vault/documents/models.py` defines the initial `Document` ORM model.
* The `Document` model includes `id`, `organization_id`,
  `uploaded_by_user_id`, `original_filename`, `stored_filename`,
  `content_type`, `file_size_bytes`, `sha256_hash`, `status`, and
  `created_at`.
* Document IDs use UUID primary keys.
* Document timestamps use the same UTC-aware application-side timestamp
  default as the existing user, organization, and membership models.
* Document metadata includes non-null constraints for all official fields.
* Document metadata uses reasonable string lengths for filenames, content
  type, SHA-256 hash, and status.
* Documents are connected to organizations through a foreign key from
  `documents.organization_id` to `organizations.id`.
* Documents are connected to uploaders through a foreign key from
  `documents.uploaded_by_user_id` to `users.id`.
* Document status metadata includes a check constraint for `pending`,
  `approved`, `rejected`, and `needs_info`.
* Document status defaults to `pending` at the model level.
* Document lookup indexes exist for organization lookup, organization/status
  lookup, and SHA-256 duplicate-detection groundwork.
* SHA-256 hash is indexed but not globally unique, so duplicate records can
  still be stored later if duplicate detection needs them.
* Shared SQLAlchemy model metadata imports `Document`, so Alembic target
  metadata includes the `documents` table.
* A create-documents migration exists at
  `alembic/versions/0004_create_documents.py`.
* The create-documents migration creates only the `documents` table and its
  supporting indexes.
* The create-documents migration downgrade drops only the `documents` table
  after dropping its supporting indexes.
* `src/vault/documents/service.py` provides typed document metadata
  creation service behavior.
* The document metadata service accepts a SQLAlchemy `Session`,
  organization ID, uploader user ID, original filename, stored filename,
  content type, file size, and SHA-256 hash.
* Document metadata creation trims small surrounding whitespace from
  metadata string fields only.
* Document metadata creation rejects blank original filenames, blank stored
  filenames, blank content types, blank SHA-256 hashes, malformed SHA-256
  hashes, and non-positive file sizes.
* SHA-256 hashes must be exactly 64 lowercase hexadecimal characters.
* Document metadata creation stores the official `pending` status value.
* Document metadata records are added to the supplied session and flushed so
  generated IDs are available.
* Document metadata creation does not commit automatically.
* Document metadata creation performs no file reads, file writes, hash
  calculation, safe filename generation, duplicate rejection, or membership
  verification yet.
* Duplicate SHA-256 hashes are still allowed because duplicate detection has
  not been implemented yet.
* No membership management API routes, organization-scoped document access
  enforcement, document uploads, document routes, upload validation helpers,
  document facts, reviews, audit logs, exports, refresh tokens, password
  reset, email verification, CI files, sample outputs, local databases beyond
  metadata migrations, or application container were added.

Current validation status:

```text
Step 16 validation was run in the uploaded runtime with partial tooling
limitations.

python -m pytest tests/test_document_service.py -q
Passed. 28 passed.

python -m pytest -q
Passed. 225 passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users,
0003_orgs_memberships, and 0004_create_documents as head.

python -m ruff check .
Could not run in this environment because Ruff is not installed in the active
runtime.

python -m mypy src scripts tests
Could not run in this environment because mypy is not installed in the active
runtime.

python -m bandit -r src
Could not run in this environment because Bandit is not installed in the active
runtime.

python -m pip_audit
Could not run in this environment because pip-audit is not installed in the
active runtime. No project vulnerability result was produced.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.

Optional Docker-backed migration smoke check
Skipped in this environment because Docker is not installed.
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
Step 17 — Secure upload validation helpers.
```


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

### Step 3 — Database configuration and Docker Compose baseline

Status: Complete with documented environment limitations.

Goal:

* Add safe database configuration helpers and a Docker Compose PostgreSQL
  baseline before models and migrations are added.

Completed work:

* Added SQLAlchemy as a runtime dependency in `pyproject.toml`.
* Added psycopg as the PostgreSQL runtime driver in `pyproject.toml`.
* Kept the existing typed dataclass settings approach instead of adding
  `pydantic-settings`, because this step does not need it yet.
* Confirmed settings include app name, environment, database URL, and upload
  directory.
* Preserved safe local defaults so imports and tests do not require real
  secrets or private environment variables.
* Updated `.env.example` with fake local PostgreSQL and upload settings only.
* Added `docker-compose.yml` with a single local PostgreSQL service.
* Configured the PostgreSQL service with environment-variable defaults, safe
  local-only credentials, a named volume, port mapping, and a healthcheck.
* Added `src/vault/database.py` with typed helpers for SQLAlchemy engine
  creation, session factory creation, and settings-based engine creation.
* Avoided global engines and import-time database connections.
* Avoided ORM models, Alembic migrations, table creation, database startup
  side effects, auth, organizations, uploads, reviews, audit logs, exports,
  CI, sample outputs, local databases, and application containers.
* Added tests for settings defaults, environment database URL loading, engine
  creation without a live database connection, settings-based engine creation,
  and session factory creation.

Files created or edited:

```text
pyproject.toml
.env.example
docker-compose.yml
src/vault/database.py
tests/test_config.py
tests/test_database_config.py
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
docker compose config
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.

python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 15 source files.

python -m pytest
12 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

docker compose config
Did not complete in this environment because Docker is not installed.

Optional Docker runtime checks
Skipped in this environment because Docker is not installed:

* docker compose up -d db
* docker compose ps
* docker compose down

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
The code validation checks that can run offline all passed. The pip-audit,
Docker, and git status limitations are environment issues from this uploaded
zip/runtime, not implemented project behavior.
```

Definition of done:

* Settings include a typed database URL.
* `.env.example` has safe local database values.
* `docker-compose.yml` defines a local PostgreSQL service.
* Database helpers can create an engine and session factory without connecting
  at import time.
* Tests cover settings and database helper behavior.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Docker checks were attempted or explicitly skipped with the reason.
* Project State is updated.

Suggested commit message:

```text
Add database configuration and Docker Compose baseline
```

---

### Step 4 — Alembic baseline

Status: In progress pending final local validation after the test isolation
patch.

Goal:

* Add Alembic migration infrastructure with an empty baseline revision so Vault
  is ready for SQLAlchemy models in the next step without creating tables yet.

Completed work:

* Added Alembic as a runtime dependency.
* Added `alembic.ini` at the repository root.
* Added `alembic/env.py`.
* Added `alembic/script.py.mako`.
* Added `alembic/versions/`.
* Added `alembic/versions/.gitkeep`.
* Added one empty baseline migration revision at
  `alembic/versions/0001_baseline.py`.
* Configured the baseline migration with `down_revision = None`.
* Kept the baseline `upgrade()` and `downgrade()` functions empty.
* Avoided table creation and ORM model implementation.
* Configured Alembic to read the database URL from Vault settings.
* Kept Alembic import/config behavior free of import-time database connections.
* Added tests for Alembic config files, versions folder, baseline revision
  count, baseline revision metadata, empty upgrade behavior, empty downgrade
  behavior, and import behavior.
* Ran optional Docker-backed Alembic smoke commands locally after setting
  `VAULT_DATABASE_URL` in PowerShell.
* Confirmed `python -m alembic upgrade head` connects to PostgreSQL and applies
  the empty baseline migration.
* Confirmed `python -m alembic current` reports `0001_baseline (head)`.

Additional local troubleshooting notes:

* Initial `python -m alembic current` failed because `psycopg` was installed
  without a usable local libpq wrapper on Windows.
* The local development fix was to install/use the binary psycopg extra.
* A later `python -m alembic current` attempt failed because the connection URL
  did not include a password.
* PowerShell requires environment variables to be set with
  `$env:VAULT_DATABASE_URL=...`, not Bash-style `VAULT_DATABASE_URL=...`.
* After Docker was running and the PowerShell environment variable was set,
  `python -m alembic upgrade head` and `python -m alembic current` passed.
* A later pytest run failed because the same PowerShell session still had
  `VAULT_DATABASE_URL` set to the Docker database URL, while the Alembic import
  test expected the safe default URL.
* The correct test fix is to clear `VAULT_DATABASE_URL` with `monkeypatch`
  inside `test_alembic_env_import_does_not_require_database_connection()`
  before loading `alembic/env.py`.

Files created or edited:

```text
pyproject.toml
alembic.ini
alembic/env.py
alembic/script.py.mako
alembic/versions/.gitkeep
alembic/versions/0001_baseline.py
src/vault/database.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run or attempted:

```bash
python -m pip install -e ".[dev]"
python -m pip install "psycopg[binary]"
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
python -m alembic current
docker compose up -d db
python -m alembic upgrade head
python -m alembic current
docker compose down
git status
```

Validation results so far:

```text
python -m alembic history
Passed. Alembic history can be read without connecting to PostgreSQL.

python -m alembic upgrade head
Passed after Docker/database URL setup. Alembic connected to the local
PostgreSQL database and applied the empty baseline migration.

python -m alembic current
Passed after Docker/database URL setup. Current revision reported as
0001_baseline (head).

python -m pytest
Failed locally after the optional Alembic smoke check because the PowerShell
session retained VAULT_DATABASE_URL. The failed test was
test_alembic_env_import_does_not_require_database_connection. It expected the
safe default URL but received the Docker URL from the shell environment. Patch
the test to clear VAULT_DATABASE_URL with monkeypatch before importing
alembic/env.py, then rerun pytest.

Remaining required validation
Pending rerun after the local test patch:

* python -m ruff check .
* python -m mypy src scripts tests
* python -m pytest
* python -m bandit -r src
* python -m pip_audit
* python scripts/run_vault.py --help
* git status
```

Validation note:

```text
Step 4 should not be marked complete until the Alembic test is patched and the
required validation suite is rerun. The Docker-backed Alembic smoke check itself
passed after the local environment was corrected.
```

Definition of done:

* Alembic is included as a project dependency.
* `alembic.ini` exists.
* Alembic environment files exist.
* Alembic versions folder exists.
* One empty baseline revision exists.
* No tables or ORM models are created in this step.
* Alembic setup uses Vault database settings safely.
* Alembic setup does not connect at import time during normal tests.
* Tests cover the Alembic baseline structure.
* Existing tests still pass after the environment-isolation test fix.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes or documented findings are explained.
* pip-audit passes or documented findings are explained.
* CLI help still works.
* Project State is updated.
* `git status` shows only expected files.
* No generated private/local files are staged.

Suggested commit message after validation passes:

```text
Add Alembic baseline
```

---


### Step 5 — Core database model base and user model

Status: Complete with documented environment limitations.

Goal:

* Add the shared SQLAlchemy model metadata path, initial `User` ORM model, and
  one Alembic migration that creates the `users` table.

Completed work:

* Added `src/vault/auth/__init__.py`.
* Added `src/vault/auth/models.py`.
* Added a typed SQLAlchemy 2-style `User` ORM model.
* Added the official user fields: `id`, `email`, `password_hash`,
  `full_name`, `is_active`, and `created_at`.
* Used UUID primary keys for users.
* Used UTC-aware application-side timestamp generation for `created_at`.
* Added non-null constraints through model metadata for all official user
  fields.
* Added a unique email rule on the user model.
* Added reasonable string lengths for email, password hash, and full name.
* Added `src/vault/models.py` as the shared model metadata import point for
  Alembic and future model registration.
* Updated `alembic/env.py` so `target_metadata` uses Vault model metadata.
* Added `alembic/versions/0002_create_users.py`.
* Kept the existing empty baseline migration unchanged.
* The create-users migration creates only the `users` table.
* The create-users migration downgrade drops only the `users` table.
* Added tests for user table name, expected columns, column lengths,
  non-nullability, email uniqueness, and metadata registration.
* Updated Alembic tests for the expected baseline plus create-users revision
  files.
* Added tests confirming the create-users migration creates only the users table
  and downgrades only the users table.
* Added a practical Alembic metadata test confirming `target_metadata` includes
  the `users` table.
* Did not add password hashing, registration, login, JWT/session behavior,
  current-user dependencies, organizations, memberships, RBAC, uploads,
  reviews, audit logs, exports, sample outputs, CI, or local databases.

Files created or edited:

```text
src/vault/auth/__init__.py
src/vault/auth/models.py
src/vault/models.py
alembic/env.py
alembic/versions/0002_create_users.py
tests/test_user_model.py
tests/test_alembic_config.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 20 source files.

python -m pytest
30 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline followed by 0002_create_users
(head).

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 5 is complete in the uploaded runtime with the documented limitations. The
offline code validation suite passed. pip-audit could not complete because this
runtime could not resolve pypi.org. Docker-backed migration checks were skipped
because Docker is not installed. git status could not run because the uploaded
zip does not include .git metadata.
```

Definition of done:

* Shared SQLAlchemy model metadata import exists.
* Alembic target metadata points at Vault model metadata.
* `User` ORM model exists.
* `users` table metadata matches the official Project State fields.
* User email has a uniqueness rule.
* No raw-password storage behavior is added.
* A create-users Alembic migration exists.
* The migration creates only the `users` table.
* The migration downgrade drops only the `users` table.
* Tests cover model structure and migration presence.
* Existing tests pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add user model and migration
```

---


### Step 6 — Password hashing and user creation service

Status: Complete with documented environment limitations.

Goal:

* Add secure password hashing helpers and a user creation service that creates
  `User` records with normalized email addresses and hashed passwords, without
  adding API routes yet.

Completed work:

* Added `argon2-cffi` as a minimal runtime dependency for modern application
  password hashing.
* Added `src/vault/auth/passwords.py`.
* Added typed `hash_password()` helper.
* Added typed `verify_password()` helper.
* Password hashes do not equal raw passwords.
* Hashing the same password twice produces different hashes because Argon2 uses
  salts.
* Password verification returns true for the original password and false for a
  wrong password.
* Added `src/vault/auth/service.py`.
* Added typed `create_user()` service function.
* The user creation service accepts a SQLAlchemy `Session`, email, raw password,
  and full name.
* User emails are normalized by trimming surrounding whitespace and lowercasing
  before storage.
* Blank email values are rejected.
* Blank password values are rejected.
* Blank full-name values are rejected.
* New users are created with `is_active` set to true.
* Raw passwords are never stored or returned by the service.
* The service stores only password hashes in the `User.password_hash` field.
* The service adds the user to the supplied session and flushes, but does not
  commit.
* Duplicate normalized email creation is rejected with `DuplicateUserError`.
* Added `ValidationError` and `DuplicateUserError` in `src/vault/exceptions.py`.
* Added `tests/test_passwords.py`.
* Added `tests/test_user_service.py`.
* Service tests use an in-memory SQLite database only for isolated unit tests.
* No database migrations were added because the `users` table did not change.
* Did not add registration routes, login routes, JWT/session behavior,
  current-user dependencies, password reset, email verification, organizations,
  memberships, RBAC, uploads, reviews, audit logs, exports, sample outputs, CI,
  or local databases.

Files created or edited:

```text
pyproject.toml
src/vault/auth/models.py
src/vault/auth/passwords.py
src/vault/auth/service.py
src/vault/exceptions.py
tests/test_passwords.py
tests/test_user_service.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.

python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 24 source files.

python -m pytest
44 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline followed by 0002_create_users
(head). No Step 6 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 6 is complete in the uploaded runtime with the documented limitations. The
offline code validation suite passed. pip-audit could not complete because this
runtime could not resolve pypi.org. Docker-backed migration checks were skipped
because Docker is not installed. git status could not run because the uploaded
zip does not include .git metadata.
```

Definition of done:

* Password hashing helper exists.
* Password verification helper exists.
* Password hashes are salted.
* User creation service exists.
* User creation normalizes email.
* User creation rejects blank required inputs.
* User creation stores password hashes only.
* No raw-password storage behavior is added.
* No auth routes are added yet.
* No token/session behavior is added yet.
* Tests cover password hashing and user creation service behavior.
* Existing tests pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add password hashing and user creation service
```

---

### Step 7 — Registration API route

Status: Complete with documented environment limitations.

Goal:

* Add a FastAPI registration endpoint that creates users through the existing
  user creation service, returns safe user data, and does not expose passwords
  or password hashes.

Completed work:

* Added `src/vault/auth/schemas.py`.
* Added `UserRegistrationRequest` with explicit `email`, `password`, and
  `full_name` fields.
* Added `UserRegistrationResponse` with safe user fields only.
* Added blank-string validation for registration request fields.
* Updated `src/vault/api/dependencies.py` with a typed database session
  dependency.
* The database session dependency yields a SQLAlchemy session and closes it
  safely.
* The database dependency creates no global connection at import time.
* Added `src/vault/api/routes/auth.py`.
* Added `POST /auth/register`.
* Included the auth router in the FastAPI app factory.
* Kept the registration route thin.
* The route calls the existing `create_user()` service.
* The route does not perform password hashing directly.
* The route commits successful user creation and refreshes the user before
  returning the response schema.
* Duplicate normalized emails return HTTP 409 with a clear client error.
* Service validation errors return HTTP 400 if they reach the route.
* Pydantic request validation rejects blank email, password, and full name with
  HTTP 422 before the service is called.
* Added `tests/test_auth_registration_api.py`.
* Route tests override the database dependency.
* Route tests use an isolated in-memory SQLite database with SQLAlchemy only for
  API tests.
* Route tests confirm successful registration returns HTTP 201.
* Route tests confirm safe response fields only.
* Route tests confirm raw passwords and password hashes are not returned.
* Route tests confirm email normalization.
* Route tests confirm a password hash is stored instead of the raw password.
* Route tests confirm blank email, blank password, and blank full name are
  rejected.
* Route tests confirm duplicate normalized email registration is rejected.
* Route tests confirm `/openapi.json` includes `/auth/register`.
* No login route, JWT/session handling, current-user dependency, password reset,
  email verification, organizations, memberships, RBAC, uploads, reviews, audit
  logs, exports, sample outputs, CI, local databases, or migration files were
  added.

Files created or edited:

```text
src/vault/api/dependencies.py
src/vault/api/main.py
src/vault/api/routes/__init__.py
src/vault/api/routes/auth.py
src/vault/auth/__init__.py
src/vault/auth/schemas.py
tests/test_auth_registration_api.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.
The command output was long enough that the container command timed out after
successful installation, but the installed tools were available afterward.

python -m ruff check .
All checks passed after import sorting was applied to the new registration API
route test file.

python -m mypy src scripts tests
Success: no issues found in 27 source files.

python -m pytest
55 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline followed by 0002_create_users
(head). No Step 7 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 7 is complete in the uploaded runtime with the documented limitations. The
offline code validation suite passed. pip-audit could not complete because this
runtime could not resolve pypi.org. Docker-backed migration checks were skipped
because Docker is not installed. git status could not run because the uploaded
zip does not include .git metadata.
```

Definition of done:

* `POST /auth/register` exists.
* Registration route calls the user creation service.
* Registration route returns HTTP 201 on success.
* Registration route returns safe user data only.
* Registration response does not expose raw passwords.
* Registration response does not expose password hashes.
* Registration rejects blank required inputs.
* Registration rejects duplicate normalized emails.
* Route tests cover success and failure cases.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add registration API route
```

### Step 8 — Login service and token foundation

Status: Complete with documented environment limitations.

Goal:

* Add login authentication service behavior and a minimal token foundation so a
  registered user can authenticate and receive an access token, without adding
  protected routes or organization logic yet.

Completed work:

* Added token-related settings to `src/vault/config.py`:
  `token_secret_key`, `token_algorithm`, and
  `access_token_expiration_minutes`.
* Kept token settings safe for local tests and documented that local defaults
  are not production secrets.
* Added `AuthenticationError` and `InactiveUserError` in
  `src/vault/exceptions.py`.
* Added `UserLoginRequest` and `UserLoginResponse` in
  `src/vault/auth/schemas.py`.
* Login requests include `email` and `password`.
* Login responses include `access_token` and `token_type`.
* Login `token_type` defaults to `bearer`.
* Blank login email and password values are rejected by schema validation.
* Added `AuthenticatedUser` as safe authenticated-user service return data.
* Added `authenticate_user()` in `src/vault/auth/service.py`.
* The login service accepts a SQLAlchemy `Session`, email, and raw password.
* The login service normalizes email before lookup.
* The login service verifies passwords through the existing password helper.
* The login service rejects wrong passwords.
* The login service rejects unknown emails.
* The login service rejects inactive users.
* The login service does not return raw passwords or password hashes.
* Added `src/vault/auth/tokens.py`.
* Added typed `create_access_token()` helper.
* Added typed `decode_access_token()` helper.
* Access-token payloads include the user ID as the `sub` subject claim.
* Access-token payloads include an `exp` expiration claim.
* Tokens are signed with HS256 using standard-library HMAC/SHA-256 helpers.
* Token validation checks token structure, signature, algorithm, token type,
  subject, and expiration.
* Added `POST /auth/login`.
* Kept the login route thin.
* The login route calls the login service.
* The login route creates an access token only after successful authentication.
* The login route does not perform password verification directly.
* The login route does not expose raw passwords or password hashes.
* Successful login returns HTTP 200.
* Wrong-password and unknown-email attempts return HTTP 401 with the same safe
  public error.
* Inactive-user login attempts return HTTP 403 with the same safe public error.
* Updated the FastAPI app description to include login as implemented behavior.
* Added service tests for login success, email normalization, wrong password,
  unknown email, inactive users, and safe service return data.
* Added token tests for token creation, decoding, subject, expiration, expired
  token rejection, and wrong-secret rejection.
* Added API tests for successful login, bearer token response, response safety,
  wrong password, unknown email, inactive users, blank fields, and OpenAPI
  inclusion.
* Added settings tests for token defaults and environment overrides.
* Existing registration behavior remains covered and passing.
* No current-user dependency, protected routes, refresh tokens, password reset,
  email verification, organizations, memberships, RBAC, uploads, reviews, audit
  logs, exports, sample outputs, CI, local databases, or migration files were
  added.

Files created or edited:

```text
src/vault/config.py
src/vault/exceptions.py
src/vault/api/main.py
src/vault/api/routes/auth.py
src/vault/auth/schemas.py
src/vault/auth/service.py
src/vault/auth/tokens.py
tests/test_auth_login_service.py
tests/test_auth_tokens.py
tests/test_auth_login_api.py
tests/test_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 31 source files.

python -m pytest
79 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline followed by 0002_create_users
(head). No Step 8 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 8 is complete in the uploaded runtime with the documented limitations. The
offline code validation suite passed. pip-audit could not complete because this
runtime could not resolve pypi.org. Docker-backed migration checks were skipped
because Docker is not installed. git status could not run because the uploaded
zip does not include .git metadata.
```

Definition of done:

* Login service behavior exists.
* Login service normalizes email.
* Login service verifies passwords through existing password helpers.
* Login service rejects invalid credentials.
* Login service rejects inactive users.
* Token creation helper exists.
* Token payload includes user ID as subject.
* Token payload includes expiration.
* `POST /auth/login` exists.
* Login route returns HTTP 200 on success.
* Login route returns a bearer access token.
* Login route does not expose raw passwords.
* Login route does not expose password hashes.
* Invalid login attempts return safe public errors.
* Tests cover login service behavior.
* Tests cover token behavior.
* Tests cover login API behavior.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add login and token foundation
```

---

### Step 9 — Current-user dependency and protected route foundation

Status: Complete with documented environment limitations.

Goal:

* Add a reusable current-user dependency that validates bearer tokens, loads the
  active user from the database, and exposes one protected route proving
  authenticated request handling works.

Completed work:

* Added a reusable `get_current_user()` dependency in
  `src/vault/api/dependencies.py`.
* The current-user dependency uses FastAPI `HTTPBearer` security utilities with
  controlled public error handling.
* The current-user dependency reads bearer credentials from the `Authorization`
  header.
* Missing bearer tokens are rejected.
* Malformed authorization headers are rejected.
* Invalid access tokens are rejected.
* Expired access tokens are rejected.
* Tokens for unknown users are rejected.
* Tokens for inactive users are rejected.
* Current-user API auth failures return a safe generic HTTP 401 response with a
  `WWW-Authenticate: Bearer` header.
* Added `load_active_user_from_token()` in `src/vault/auth/service.py`.
* The token-to-user helper decodes the existing access token format.
* The token-to-user helper extracts the token subject and parses it as a UUID.
* The token-to-user helper loads the matching `User` from the supplied database
  session.
* The token-to-user helper requires the user to exist and be active.
* Added `CurrentUserResponse` in `src/vault/auth/schemas.py`.
* Added `GET /auth/me`.
* Kept the protected route thin.
* `GET /auth/me` depends on the current-user dependency.
* `GET /auth/me` returns `id`, `email`, `full_name`, `is_active`, and
  `created_at`.
* `GET /auth/me` does not return raw passwords.
* `GET /auth/me` does not return password hashes.
* Updated the FastAPI app description to include current-user lookup as current
  implemented behavior.
* Added `tests/test_current_user_dependency.py`.
* Added `tests/test_auth_me_api.py`.
* Dependency tests cover missing credentials, malformed credentials, invalid
  tokens, expired tokens, unknown-user tokens, inactive-user tokens, and valid
  active-user resolution.
* API tests cover missing token, malformed authorization header, invalid token,
  expired token, valid token, safe response fields, password exclusion,
  password-hash exclusion, unknown-user token rejection, inactive-user token
  rejection, and OpenAPI inclusion.
* Existing Step 1 through Step 8 tests remain passing.
* No database migrations were added because the `users` table did not change.
* No organizations, memberships, role-based authorization, organization-scoped
  data access, document uploads, document metadata, reviews, audit logs,
  exports, refresh tokens, password reset, email verification, sample outputs,
  CI, local databases, or application container were added.

Files created or edited:

```text
src/vault/api/dependencies.py
src/vault/api/main.py
src/vault/api/routes/auth.py
src/vault/auth/schemas.py
src/vault/auth/service.py
tests/test_current_user_dependency.py
tests/test_auth_me_api.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed far enough to install required runtime and development tools. The output
was long enough that the first combined install command timed out after package
installation activity, so missing validation tools were installed directly and
the validation suite was rerun.

python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 33 source files.

python -m pytest
97 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline followed by 0002_create_users
(head). No Step 9 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 9 is complete in the uploaded runtime with the documented limitations. The
offline code validation suite passed. pip-audit could not complete because this
runtime could not resolve pypi.org. Docker-backed migration checks were skipped
because Docker is not installed. git status could not run because the uploaded
zip does not include .git metadata.
```

Definition of done:

* Current-user dependency exists.
* Current-user dependency validates bearer access tokens.
* Current-user dependency loads the active user from the database.
* Missing tokens are rejected.
* Invalid tokens are rejected.
* Expired tokens are rejected.
* Unknown-user tokens are rejected.
* Inactive-user tokens are rejected.
* `GET /auth/me` exists.
* `GET /auth/me` returns safe current-user data.
* `GET /auth/me` does not expose raw passwords.
* `GET /auth/me` does not expose password hashes.
* Route and dependency tests cover success and failure cases.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add current-user dependency
```

---

### Step 10 — Organization model and membership model

Status: Complete with documented environment limitations.

Goal:

* Add initial organization and membership SQLAlchemy models, official role
  values, and one Alembic migration that creates the organization tables.

Completed work:

* Added `src/vault/organizations/__init__.py`.
* Added `src/vault/organizations/roles.py`.
* Defined official membership role values as `owner`, `reviewer`, and `viewer`.
* Added `src/vault/organizations/models.py`.
* Added a typed SQLAlchemy 2-style `Organization` ORM model.
* Added the official organization fields: `id`, `name`,
  `created_by_user_id`, and `created_at`.
* Added a typed SQLAlchemy 2-style `Membership` ORM model.
* Added the official membership fields: `id`, `organization_id`, `user_id`,
  `role`, and `created_at`.
* Used UUID primary keys for organizations and memberships.
* Used the existing UTC-aware timestamp helper for organization and membership
  `created_at` defaults.
* Added non-null constraints for all official organization and membership
  fields.
* Added reasonable string lengths for organization names and membership roles.
* Added a foreign key from `organizations.created_by_user_id` to `users.id`.
* Added a foreign key from `memberships.organization_id` to
  `organizations.id`.
* Added a foreign key from `memberships.user_id` to `users.id`.
* Added a uniqueness rule preventing duplicate memberships for the same user in
  the same organization.
* Added membership lookup indexes for organization ID and user ID.
* Added a membership role check constraint for `owner`, `reviewer`, and
  `viewer`.
* Updated `src/vault/models.py` so shared model metadata imports `User`,
  `Organization`, and `Membership`.
* Confirmed Alembic target metadata includes `users`, `organizations`, and
  `memberships`.
* Added `alembic/versions/0003_orgs_memberships.py`.
* The new migration creates only the `organizations` and `memberships` tables.
* The migration downgrade drops only `memberships` and `organizations`, with
  the child table dropped before the parent table.
* Added `tests/test_organization_models.py`.
* Updated Alembic tests to expect the new migration file.
* Added tests for organization columns, membership columns, non-nullability,
  UUID-style IDs, role values, role constraint metadata, foreign keys, duplicate
  membership uniqueness, metadata registration, and migration behavior.
* Existing Step 1 through Step 9 tests remain passing.
* No organization routes, services, RBAC dependency, scoped data enforcement,
  invitations, document uploads, reviews, audit logging, exports, sample
  outputs, CI, or local databases were added.

Files created or edited:

```text
src/vault/organizations/__init__.py
src/vault/organizations/models.py
src/vault/organizations/roles.py
src/vault/models.py
alembic/versions/0003_orgs_memberships.py
tests/test_organization_models.py
tests/test_alembic_config.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 37 source files.

python -m pytest
117 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users, and
0003_orgs_memberships as head.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 10 is complete in the uploaded runtime with the documented limitations.
The offline code validation suite passed. pip-audit could not complete because
this runtime could not resolve pypi.org. Docker-backed migration checks were
skipped because Docker is not installed. git status could not run because the
uploaded zip does not include .git metadata.
```

Definition of done:

* `Organization` ORM model exists.
* `Membership` ORM model exists.
* Official role values are defined.
* Organization model matches the Project State fields.
* Membership model matches the Project State fields.
* Foreign keys connect organizations and memberships to users correctly.
* Duplicate user membership in the same organization is prevented by metadata.
* New models are registered in shared Vault model metadata.
* Alembic target metadata includes the new tables.
* A migration creates only organizations and memberships.
* The migration downgrade drops only memberships and organizations.
* No organization routes are added yet.
* No RBAC enforcement is added yet.
* Tests cover model structure, role values, constraints, metadata, and migration
  presence.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add organization and membership models
```

---

### Step 11 — Organization creation service

Status: Complete with documented environment limitations.

Goal:

* Add an organization creation service that creates an organization and assigns
  the creator an owner membership in one transaction, without adding API routes
  yet.

Completed work:

* Added `src/vault/organizations/service.py`.
* Added `OrganizationCreation` as a small typed service result containing the
  created organization and owner membership.
* Added typed `create_organization()` service function.
* The service accepts a SQLAlchemy `Session`, creator `User` ORM object, and
  organization name.
* Organization names are normalized by trimming surrounding whitespace.
* Blank and whitespace-only organization names are rejected with
  `OrganizationValidationError`.
* Inactive creator users are rejected with `OrganizationValidationError`.
* Organization creation sets `created_by_user_id` to the creator user's ID.
* Organization creation creates an owner membership for the creator.
* The owner membership uses the official `MembershipRole.OWNER.value` role
  value.
* Organization and membership records are added to the same supplied session.
* The service flushes so organization and membership IDs are available to the
  caller.
* The service does not commit automatically.
* Added `OrganizationError` and `OrganizationValidationError` in
  `src/vault/exceptions.py`.
* Added `tests/test_organization_service.py`.
* Service tests use an isolated in-memory SQLite database only for unit tests.
* Tests cover trimmed names, creator user ID, owner membership creation,
  official owner role value, generated IDs after flush, blank-name rejection,
  whitespace-only-name rejection, inactive creator rejection, no automatic
  commit, shared-session behavior, and duplicate membership constraint behavior.
* Existing Step 1 through Step 10 tests remain passing.
* No organization API routes, membership API routes, RBAC dependency,
  organization-scoped data access enforcement, invitations, document uploads,
  reviews, audit logging, exports, sample outputs, CI, local databases, or
  migrations were added.

Files created or edited:

```text
src/vault/organizations/service.py
src/vault/exceptions.py
tests/test_organization_service.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 39 source files.

python -m pytest
128 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment. pip-audit was installed and run, but
failed while trying to resolve pypi.org due to DNS/network access. No project
vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users, and
0003_orgs_memberships as head. No Step 11 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 11 is complete in the uploaded runtime with the documented limitations.
The offline code validation suite passed. pip-audit could not complete because
this runtime could not resolve pypi.org. Docker-backed migration checks were
skipped because Docker is not installed. git status could not run because the
uploaded zip does not include .git metadata.
```

Definition of done:

* Organization creation service exists.
* Service trims organization names.
* Blank organization names are rejected.
* Inactive creator users are rejected.
* Service creates an `Organization`.
* Service creates an owner `Membership` for the creator.
* Organization and membership are added in the same session.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* No organization routes are added yet.
* No RBAC enforcement is added yet.
* No migrations are added in this step.
* Tests cover organization creation service behavior.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add organization creation service
```

---

### Step 12 — Organization creation API route

Status: Implementation complete; final local validation results need to be
confirmed in this Project State file after the validation suite is rerun.

Goal:

* Add an authenticated organization creation API route that uses the existing
  current-user dependency and existing organization creation service to create
  an organization for the logged-in user.

Completed work:

* Added `src/vault/api/routes/organizations.py`.
* Added an authenticated `POST /organizations` endpoint.
* Included the organizations router in the FastAPI app factory.
* Kept the organization creation route thin.
* The route depends on the existing current-user dependency.
* The route depends on the existing database session dependency.
* The route calls the existing `create_organization()` service.
* The route does not manually create `Organization` or `Membership` ORM
  records.
* The route commits successful organization creation.
* The route refreshes the created organization and owner membership before
  returning.
* Added `src/vault/organizations/schemas.py`.
* Added an organization creation request schema with `name`.
* Added an organization creation response schema with safe organization data:
  `id`, `name`, `created_by_user_id`, and `created_at`.
* Included owner membership data in the organization creation response:
  `membership_id` and `role`.
* The response does not include raw passwords, password hashes, token payload
  internals, or unrelated user data.
* Successful organization creation returns HTTP 201.
* Missing bearer tokens return HTTP 401.
* Invalid bearer tokens return HTTP 401.
* Expired bearer tokens return HTTP 401.
* Inactive authenticated users cannot create organizations.
* Blank organization names are rejected.
* Whitespace-only organization names are rejected.
* Duplicate organization names are not rejected in this step because no
  uniqueness rule exists for organization names yet.
* No database migration was added in this step.
* No RBAC checks were added beyond requiring an authenticated active user.
* No organization-scoped authorization is claimed complete yet.
* Added `tests/test_organization_create_api.py`.
* API tests cover missing token, invalid token, expired token, valid token,
  returned organization ID, trimmed organization name, creator user ID, owner
  role, database organization persistence, database owner membership
  persistence, official `owner` role value, blank-name rejection,
  whitespace-only-name rejection, inactive-user rejection, password exclusion,
  password-hash exclusion, and OpenAPI inclusion.
* Existing Step 1 through Step 11 behavior should remain passing.
* No listing organizations, reading organization detail, updating
  organizations, deleting organizations, inviting members, removing members,
  changing member roles, RBAC enforcement dependency, organization-scoped data
  access enforcement, document uploads, document metadata, reviews, audit logs,
  exports, sample outputs, CI, local databases, or migrations were added.

Files created or edited:

```text
src/vault/api/main.py
src/vault/api/routes/organizations.py
src/vault/organizations/schemas.py
tests/test_organization_create_api.py
docs/Project_State.md
```

Commands to run:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
git status
```

Optional Docker-backed migration smoke check if Docker is available locally:

```bash
docker compose up -d db
python -m alembic upgrade head
python -m alembic current
docker compose down
```

Validation results:

```text
Final Step 12 local validation output has not been documented in this
regenerated Project State file yet.

Update this section after local validation is rerun or pasted.

Expected checks:

python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
git status

Docker-backed migration checks should be documented as run or skipped.
```

Validation note:

```text
The Step 12 implementation is present in this regenerated Project State file,
but final local validation results should be filled in before treating this file
as the final completed Step 12 record.
```

Definition of done:

* `POST /organizations` exists.
* The route requires authentication.
* The route uses the current-user dependency.
* The route uses the database session dependency.
* The route calls the existing organization creation service.
* The route returns HTTP 201 on success.
* The route commits successful organization creation.
* The response returns safe organization data.
* The response does not expose raw passwords.
* The response does not expose password hashes.
* Blank organization names are rejected.
* Whitespace-only organization names are rejected.
* Invalid, missing, and expired tokens are rejected.
* Inactive users cannot create organizations.
* Successful creation stores an organization.
* Successful creation stores an owner membership for the creator.
* Tests cover success and failure cases.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes or documented findings are explained.
* pip-audit passes or documented findings are explained.
* CLI help still works.
* Alembic history still works.
* Project State is updated.
* `git status` shows only expected files.
* No generated private/local files are staged.

Suggested commit message:

```text
Add organization creation API route
```

---


### Step 13 — Organization membership access helpers

Status: Complete with documented environment limitations.

Goal:

* Add service-layer membership access helpers that can answer whether a user is
  a member of an organization and whether the user has an allowed role, without
  adding full RBAC route enforcement yet.

Completed work:

* Added typed `get_membership_for_user()` helper in
  `src/vault/organizations/service.py`.
* `get_membership_for_user()` returns the matching `Membership` when the user
  belongs to the organization.
* `get_membership_for_user()` returns `None` when the user is not a member.
* Added typed `require_membership()` helper.
* `require_membership()` returns the matching membership when it exists.
* `require_membership()` raises `OrganizationMembershipRequiredError` when the
  user is not a member or the organization is unknown.
* Added typed `membership_has_role()` helper.
* `membership_has_role()` checks only explicitly allowed roles.
* Added typed `require_membership_role()` helper.
* `require_membership_role()` requires both membership and an explicitly
  allowed role.
* Added `OrganizationAccessError`, `OrganizationMembershipRequiredError`, and
  `OrganizationRoleRequiredError` in `src/vault/exceptions.py`.
* Kept public access error messages safe and generic.
* Role checks use official role values from
  `src/vault/organizations/roles.py`.
* Owner is not automatically allowed when only reviewer is allowed.
* Reviewer is not automatically allowed when only owner is allowed.
* Viewer is not automatically allowed when owner or reviewer is required.
* Multiple allowed roles are supported.
* Unknown allowed-role values fail closed.
* Unknown membership role values fail closed.
* Added `tests/test_organization_access_service.py`.
* Tests cover membership lookup, required membership, role checks, role denial,
  explicit role behavior, multiple allowed roles, official role values, and
  fail-closed behavior.
* Existing Step 1 through Step 12 tests remain passing in this runtime.
* No API route RBAC dependency, organization-scoped document access, membership
  invitation route, membership removal route, membership role-change route,
  document uploads, reviews, audit logs, exports, sample outputs, CI files,
  local databases, or migrations were added.

Files created or edited:

```text
src/vault/organizations/service.py
src/vault/exceptions.py
tests/test_organization_access_service.py
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
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 43 source files.

python -m pytest
161 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment because pypi.org could not be resolved.
No project vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users, and
0003_orgs_memberships as head. No Step 13 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 13 is complete in the uploaded runtime with the documented limitations.
The offline code validation suite passed. pip-audit could not complete because
this runtime could not resolve pypi.org. Docker-backed migration checks were
skipped because Docker is not installed. git status could not run because the
uploaded zip does not include .git metadata.
```

Definition of done:

* Membership lookup helper exists.
* Required membership helper exists.
* Role-check helper exists.
* Required-role helper exists.
* Helpers use official role values.
* Non-members are rejected.
* Unknown organizations fail closed.
* Role checks fail closed.
* Owner is not automatically allowed unless explicitly included.
* Reviewer is not automatically allowed unless explicitly included.
* Viewer is not automatically allowed unless explicitly included.
* No API route RBAC enforcement is added yet.
* No migrations are added in this step.
* Tests cover membership lookup, required membership, role checks, and failure
  cases.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add organization membership access helpers
```

### Step 14 — Organization RBAC route dependency

Status: Complete with documented environment limitations.

Goal:

* Add reusable FastAPI route dependencies for organization membership and role
  checks, proving route-level RBAC can be enforced before document routes are
  added.

Completed work:

* Added reusable `require_organization_roles()` dependency factory in
  `src/vault/api/dependencies.py`.
* The dependency factory accepts explicit allowed `MembershipRole` values.
* The dependency combines the authenticated current user, database session,
  `organization_id` path parameter, and required role set.
* The returned dependency calls the Step 13 `require_membership_role()` service
  helper.
* The returned dependency returns the matching `Membership` when access is
  allowed.
* Non-members are rejected with HTTP 403.
* Unknown organizations are rejected with HTTP 403 the same way as non-members.
* Members with the wrong role are rejected with HTTP 403.
* Access-denied public errors stay safe and generic.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens still
  return the existing HTTP 401 authentication error from the current-user
  dependency before organization RBAC runs.
* Owner is not treated as all-powerful; owner is allowed only when owner is
  explicitly included in the allowed roles.
* Reviewer is allowed only when reviewer is explicitly included.
* Viewer is allowed only when viewer is explicitly included.
* Multiple allowed roles are supported.
* Added thin `GET /organizations/{organization_id}` route.
* `GET /organizations/{organization_id}` uses the new organization RBAC
  dependency with owner, reviewer, and viewer all explicitly allowed.
* `GET /organizations/{organization_id}` returns safe organization detail only:
  `id`, `name`, `created_by_user_id`, and `created_at`.
* `GET /organizations/{organization_id}` does not list members, expose unrelated
  users, or implement update/delete behavior.
* Added `tests/test_organization_rbac_dependency.py`.
* Dependency tests define small test-only RBAC probe routes for owner-only,
  reviewer-only, viewer-only, and owner-or-reviewer checks.
* Tests cover allowed owner, reviewer, and viewer access.
* Tests cover non-member denial, unknown-organization denial, wrong-role denial,
  explicit-role behavior, multiple allowed roles, and returned membership data.
* Tests cover missing, invalid, expired, and inactive-user tokens preserving
  HTTP 401 authentication behavior.
* Tests cover the production organization detail route returning safe data,
  rejecting non-members, and appearing in OpenAPI.
* Existing Step 1 through Step 13 tests remain passing in this runtime.
* No migrations were added in this step.
* No document uploads, document metadata, document facts, control flags,
  duplicate detection, review workflow, audit logging, exports, sample outputs,
  CI files, local databases, or membership management routes were added.

Files created or edited:

```text
src/vault/api/dependencies.py
src/vault/api/routes/organizations.py
tests/test_organization_rbac_dependency.py
docs/Project_State.md
```

Commands run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check . --fix
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.

python -m ruff check . --fix
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 44 source files.

python -m pytest
181 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment because pypi.org could not be resolved.
No project vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users, and
0003_orgs_memberships as head. No Step 14 migration was added.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 14 is complete in the uploaded runtime with the documented limitations.
The offline code validation suite passed. pip-audit could not complete because
this runtime could not resolve pypi.org. Docker-backed migration checks were
skipped because Docker is not installed. git status could not run because the
uploaded zip does not include .git metadata.
```

Definition of done:

* Reusable organization RBAC route dependency exists.
* Dependency uses current-user authentication.
* Dependency uses database session dependency.
* Dependency uses organization membership access helpers.
* Dependency supports explicit allowed-role sets.
* Non-members are rejected.
* Unknown organizations are rejected.
* Wrong-role members are rejected.
* Allowed-role members are permitted.
* Owner is not automatically allowed unless explicitly included.
* Reviewer is not automatically allowed unless explicitly included.
* Viewer is not automatically allowed unless explicitly included.
* Missing/invalid/expired tokens still produce authentication errors.
* Access failures are safe and generic.
* No document routes are added yet.
* No migrations are added in this step.
* Tests cover allowed access, denied access, wrong roles, unknown orgs,
  non-members, and authentication failure behavior.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help still works.
* Alembic history still works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add organization RBAC route dependency
```


### Step 15 — Document metadata model and migration

Status: Complete with documented environment limitations.

Goal:

* Add the initial document metadata SQLAlchemy model and one Alembic migration
  that creates the `documents` table, without adding upload behavior yet.

Completed work:

* Added `src/vault/documents/__init__.py`.
* Added `src/vault/documents/statuses.py`.
* Defined official document status values as `pending`, `approved`,
  `rejected`, and `needs_info`.
* Added `DocumentStatus` as a small `StrEnum`.
* Added `STATUS_VALUES` as the explicit tuple of allowed document statuses.
* Added `src/vault/documents/models.py`.
* Added a typed SQLAlchemy 2-style `Document` ORM model.
* Added the official document fields: `id`, `organization_id`,
  `uploaded_by_user_id`, `original_filename`, `stored_filename`,
  `content_type`, `file_size_bytes`, `sha256_hash`, `status`, and
  `created_at`.
* Used UUID primary keys for documents.
* Used the existing UTC-aware timestamp helper for `Document.created_at`.
* Added non-null constraints for all official document fields.
* Added reasonable string lengths for original filename, stored filename,
  content type, SHA-256 hash, and status.
* Added a foreign key from `documents.organization_id` to `organizations.id`.
* Added a foreign key from `documents.uploaded_by_user_id` to `users.id`.
* Added a document status check constraint for the official status values.
* Added a model-level default status of `pending`.
* Added an organization lookup index for documents.
* Added an organization/status lookup index for future review queues.
* Added a non-unique SHA-256 hash index as duplicate-detection groundwork.
* Did not force global SHA-256 uniqueness, because duplicate detection may need
  to preserve duplicate document records later.
* Updated `src/vault/models.py` so shared model metadata imports `Document`.
* Confirmed Alembic target metadata includes `documents` through the shared
  Vault model metadata path.
* Added `alembic/versions/0004_create_documents.py`.
* The new migration creates only the `documents` table and its supporting
  indexes.
* The migration downgrade drops only the `documents` table after dropping its
  supporting indexes.
* Updated Alembic tests to expect the new migration file.
* Added tests for document table name, expected columns, column lengths,
  non-nullability, UUID-style ID metadata, UTC-aware timestamp behavior,
  official status values, default status, status check constraint, foreign keys,
  lookup indexes, model metadata registration, migration creation behavior, and
  migration downgrade behavior.
* Existing Step 1 through Step 14 tests remain passing in this runtime.
* No file upload route, upload service, file validation, safe stored filename
  generation, file hashing behavior, document facts, control flags, duplicate
  detection, review decisions, audit logging, CSV exports, sample outputs, CI
  files, local databases, or application container were added.

Files created or edited:

```text
src/vault/documents/__init__.py
src/vault/documents/models.py
src/vault/documents/statuses.py
src/vault/models.py
alembic/versions/0004_create_documents.py
tests/test_document_model.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m ruff check . --fix
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
python scripts/run_vault.py --help
python -m alembic history
docker --version
git status --short
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.

python -m ruff check .
Initially reported one import-sort issue in src/vault/documents/models.py.

python -m ruff check . --fix
Fixed the import ordering issue.

python -m ruff check .
All checks passed.

python -m mypy src scripts tests
Success: no issues found in 48 source files.

python -m pytest
197 passed.

python -m bandit -r src
No issues identified.

python -m pip_audit
Did not complete in this environment because pypi.org could not be resolved.
No project vulnerability result was produced.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users,
0003_orgs_memberships, and 0004_create_documents as head.

docker --version
Docker is not installed in this environment, so the optional Docker-backed
migration smoke check was skipped.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.
```

Validation note:

```text
Step 15 is complete in the uploaded runtime with the documented limitations.
The offline code validation suite passed. pip-audit could not complete because
this runtime could not resolve pypi.org. Docker-backed migration checks were
skipped because Docker is not installed. git status could not run because the
uploaded zip does not include .git metadata.
```

Definition of done:

* `Document` ORM model exists.
* Official document status values are defined.
* Document model matches the Project State fields.
* Foreign keys connect documents to organizations and users correctly.
* New model is registered in shared Vault model metadata.
* Alembic target metadata includes the new table.
* A migration creates only the `documents` table.
* The migration downgrade drops only the `documents` table.
* No upload behavior is added yet.
* No document routes are added yet.
* No document facts are added yet.
* No audit logging is added yet.
* Tests cover model structure, status values, constraints, metadata, and
  migration presence.
* Existing tests still pass.
* Ruff passes.
* Mypy passes.
* Pytest passes.
* Bandit passes.
* pip-audit was run and the DNS/network limitation is documented.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document metadata model
```

### Step 16 — Document metadata service

Status: Complete with documented environment limitations.

Goal:

* Add a directly testable document metadata service that can create document
  metadata records after upload validation has already happened, without adding
  actual file upload handling yet.

Completed work:

* Added `src/vault/documents/service.py`.
* Added typed `create_document_metadata()` service function.
* The service accepts a SQLAlchemy `Session`.
* The service accepts `organization_id`, `uploaded_by_user_id`,
  `original_filename`, `stored_filename`, `content_type`, `file_size_bytes`,
  and `sha256_hash`.
* The service creates a `Document` metadata record.
* The service sets status to the official `pending` document status value.
* The service adds the document to the provided session.
* The service flushes so the document ID is available to the caller.
* The service does not commit automatically.
* The service performs no file reads or writes.
* The service does not calculate hashes yet.
* The service trims surrounding whitespace from metadata string fields only.
* The service rejects blank `original_filename` values.
* The service rejects blank `stored_filename` values.
* The service rejects blank `content_type` values.
* The service rejects blank `sha256_hash` values.
* The service rejects non-positive `file_size_bytes` values.
* The service rejects malformed SHA-256 hashes.
* SHA-256 hashes must be exactly 64 lowercase hexadecimal characters.
* Duplicate SHA-256 hashes are allowed for now.
* Organization membership is not verified in this service yet.
* Added `DocumentError` and `DocumentValidationError` in
  `src/vault/exceptions.py`.
* Added `tests/test_document_service.py`.
* Service tests use an isolated in-memory SQLite database only for unit tests.
* Tests cover stored organization ID, uploader user ID, original filename,
  stored filename, content type, file size, SHA-256 hash, default pending
  status, generated ID after flush, no automatic commit, blank required string
  rejection, malformed hash rejection, zero and negative file-size rejection,
  duplicate-hash allowance, official pending status use, and no file creation
  on disk.
* Existing Step 1 through Step 15 tests remain passing in this runtime.
* No upload route, multipart handling, upload validation helper, file type
  validation, file extension validation, file size validation helper, safe
  stored filename generation, hash calculation from bytes, document facts,
  control flags, duplicate detection, review decisions, audit logging, CSV
  exports, sample outputs, CI files, local databases, migrations, or
  application container were added.

Files created or edited:

```text
src/vault/documents/service.py
src/vault/exceptions.py
tests/test_document_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_service.py -q
python -m pytest -q
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
```

Validation results:

```text
python -m pytest tests/test_document_service.py -q
28 passed.

python -m pytest -q
225 passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users,
0003_orgs_memberships, and 0004_create_documents as head.

python -m ruff check .
Could not run in this environment because Ruff is not installed in the active
runtime.

python -m mypy src scripts tests
Could not run in this environment because mypy is not installed in the active
runtime.

python -m bandit -r src
Could not run in this environment because Bandit is not installed in the active
runtime.

python -m pip_audit
Could not run in this environment because pip-audit is not installed in the
active runtime. No project vulnerability result was produced.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.

Optional Docker-backed migration smoke check
Skipped in this environment because Docker is not installed.
```

Validation note:

```text
Step 16 is complete in the uploaded runtime with documented tooling
limitations. Pytest, CLI help, and Alembic history passed. Ruff, mypy, Bandit,
pip-audit, git status, and Docker-backed migration checks should be run locally
before committing.
```

Definition of done:

* Document metadata creation service exists.
* Service creates a `Document` record.
* Service sets status to `pending`.
* Service stores metadata fields.
* Service validates obvious bad metadata.
* Service rejects blank filenames, blank content type, blank hash, malformed
  hash, and non-positive file size.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* Service performs no file I/O.
* Duplicate SHA-256 hashes are still allowed.
* No upload route is added yet.
* No upload validation helper is added yet.
* No document facts are added yet.
* No audit logging is added yet.
* No migrations are added in this step.
* Tests cover document metadata service behavior.
* Existing tests still pass.
* Pytest passes.
* CLI help works.
* Alembic history works.
* Ruff, mypy, Bandit, and pip-audit need local validation because those tools
  were unavailable in the uploaded runtime.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document metadata service
```

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
