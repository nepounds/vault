# Vault Step Plan

Vault should be built in small, testable steps. Each step updates `docs/Project_State.md` before completion.

## Phase 0 — Planning

### Step 0 — Planning docs

Create the initial planning files:

- `README.md`
- `docs/Architecture.md`
- `docs/Step_Plan.md`
- `docs/Project_State.md`

Definition of done:

- Project goal is clear.
- MVP scope is clear.
- Non-goals are clear.
- Architecture direction is clear.
- Validation commands are listed.

Suggested commit:

```text
Add Vault planning docs
```

## Phase 1 — Foundation

### Step 1 — Project skeleton and tooling

Create:

- `pyproject.toml`
- `.gitignore`
- `.env.example`
- `src/vault/__init__.py`
- `src/vault/config.py`
- `src/vault/exceptions.py`
- `scripts/__init__.py`
- `scripts/run_vault.py`
- `tests/test_package_import.py`

Add development tools:

- pytest
- ruff
- mypy
- bandit
- pip-audit if practical

Definition of done:

- Package imports.
- Tooling commands run or documented.
- First smoke test passes.

Suggested commit:

```text
Add project skeleton and tooling baseline
```

### Step 2 — FastAPI app shell

Create:

- `src/vault/api/main.py`
- health route
- root route
- shared error handling
- API smoke tests

Definition of done:

- FastAPI app imports.
- `/health` returns OK.
- Tests use FastAPI test client.

Suggested commit:

```text
Add FastAPI app shell
```

### Step 3 — Docker Compose and database connection

Create:

- `docker-compose.yml`
- database settings
- SQLAlchemy engine/session helpers
- database connection tests using isolated test database strategy

Definition of done:

- App can be configured for PostgreSQL.
- Tests do not require private local paths.
- `.env.example` documents required values.

Suggested commit:

```text
Add database configuration
```

### Step 4 — Alembic migrations baseline

Create:

- Alembic config
- migration environment
- first empty migration or metadata-connected baseline

Definition of done:

- Migrations can run locally.
- Project State documents migration commands.

Suggested commit:

```text
Add migration baseline
```

## Phase 2 — Users, auth, and organizations

### Step 5 — User model and password hashing

Add:

- user table/model
- password hashing helpers
- password verification tests
- user creation service

Definition of done:

- Raw passwords are never stored.
- Duplicate email handling is tested.

Suggested commit:

```text
Add user model and password hashing
```

### Step 6 — Registration and login

Add:

- registration route
- login route
- token/session creation
- current-user dependency
- auth tests

Definition of done:

- Valid users can register and log in.
- Invalid credentials fail safely.
- Protected route rejects anonymous requests.

Suggested commit:

```text
Add registration and login
```

### Step 7 — Organizations and memberships

Add:

- organization model
- membership model
- owner/reviewer/viewer roles
- create organization service
- membership tests

Definition of done:

- Creating an org creates owner membership.
- Membership lookup is tested.

Suggested commit:

```text
Add organizations and memberships
```

### Step 8 — Role-based authorization

Add:

- permission helper functions
- route dependencies for org roles
- tests proving viewers cannot mutate state
- tests proving outsiders cannot access org data

Definition of done:

- Organization scoping is enforced in services.
- Permission failures are clear.

Suggested commit:

```text
Add role-based authorization
```

## Phase 3 — Document intake

### Step 9 — Document model and metadata

Add:

- documents table/model
- status enum
- metadata schema
- create document metadata service

Definition of done:

- Document records are scoped to organizations.
- Status defaults to pending.

Suggested commit:

```text
Add document metadata model
```

### Step 10 — Secure upload validation

Add:

- upload endpoint
- file size validation
- extension allowlist
- detected content validation
- safe stored filename generation
- SHA-256 hash generation
- upload tests

Definition of done:

- Bad file types fail.
- Oversized files fail.
- Filenames are not trusted.
- Files are stored outside source tree.

Suggested commit:

```text
Add secure document upload validation
```

### Step 11 — Structured document facts

Add:

- document facts model
- fake invoice/receipt input schema
- validation for amount/date/vendor/category
- tests for bad accounting fields

Definition of done:

- Facts can be attached to pending documents.
- Amounts use integer cents.
- Invalid facts fail clearly.

Suggested commit:

```text
Add structured document facts
```

## Phase 4 — Controls and review workflow

### Step 12 — Accounting control flags

Add:

- control flag model
- missing required field checks
- amount threshold checks
- unapproved vendor placeholder check
- tests for generated flags

Definition of done:

- Control checks return reasoned flags.
- Flag severity is consistent.

Suggested commit:

```text
Add accounting control checks
```

### Step 13 — Duplicate detection

Add duplicate checks using:

- file hash
- vendor + invoice number
- vendor + amount + close date

Definition of done:

- Exact duplicates are flagged.
- Near duplicates are flagged with explanation.
- False-positive boundaries are tested.

Suggested commit:

```text
Add duplicate document detection
```

### Step 14 — Review decisions

Add:

- review decision model
- approve/reject/needs_info service
- legal status transitions
- required decision reason
- role tests

Definition of done:

- Reviewers and owners can review.
- Viewers cannot review.
- Decisions create audit entries.

Suggested commit:

```text
Add document review workflow
```

## Phase 5 — Audit and exports

### Step 15 — Immutable audit log

Add:

- audit entry model
- audit service
- audit query route
- audit tests for state-changing actions

Definition of done:

- Important actions write audit entries.
- Audit entries are organization-scoped.
- Normal services do not update existing audit rows.

Suggested commit:

```text
Add immutable audit logging
```

### Step 16 — CSV exports

Add:

- approved documents export
- exceptions report export
- audit log export
- sample outputs
- export tests

Definition of done:

- Exports include fake sample data only.
- Sample outputs are current.
- Export commands/routes are tested.

Suggested commit:

```text
Add CSV exports and sample outputs
```

## Phase 6 — CLI, docs, and CI

### Step 17 — Thin CLI helper

Add CLI commands for local demo workflows:

- seed demo data
- export reports
- run control checks if useful

Definition of done:

- CLI calls services.
- CLI does not own business logic.

Suggested commit:

```text
Add local demo CLI
```

### Step 18 — CI workflow

Add GitHub Actions CI:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
```

Add pip-audit if dependency setup is stable enough.

Definition of done:

- CI mirrors local validation.
- README badge can be added after CI exists.

Suggested commit:

```text
Add CI workflow
```

### Step 19 — README quickstart and screenshots

Polish docs after behavior exists:

- quickstart
- endpoint examples
- demo user credentials for fake data
- screenshots if UI exists
- sample output explanation

Definition of done:

- A stranger can clone and run the happy path.
- README does not claim unbuilt features.

Suggested commit:

```text
Polish README quickstart
```

### Step 20 — Final hardening cleanup

Run and fix:

- Ruff
- mypy
- pytest
- Bandit
- pip-audit
- sample-output drift review
- git status review

Definition of done:

- Project State is marked complete.
- Known limitations are documented honestly.
- Final repo is portfolio-ready.

Suggested commit:

```text
Add final hardening cleanup
```
