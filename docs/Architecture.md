# Vault Architecture

Vault is a secure accounting document workflow web app.

The architecture goal is simple: keep business rules testable, keep web handlers thin, and make every state-changing action go through an official service layer that writes an audit log entry.

## Core design

Vault uses a layered FastAPI application:

```text
HTTP route
  -> request schema
  -> service function
  -> authorization check
  -> domain validation
  -> database transaction
  -> audit log entry
  -> response schema
```

Routes should not own business rules. They should parse input, call services, and return responses.

## Main modules

```text
src/vault/
├── api/              FastAPI app, routes, dependencies, error handlers
├── auth/             password hashing, token/session logic, current-user dependency
├── organizations/    organization creation, membership, role checks
├── documents/        upload validation, metadata, document records
├── reviews/          review queue, decisions, status transitions
├── controls/         accounting-control checks and duplicate detection
├── audit/            immutable audit log creation and queries
├── exports/          CSV export builders
├── config.py         settings and environment loading
├── database.py       engine/session helpers
└── exceptions.py     custom project exceptions
```

## Data model draft

### users

| Field | Notes |
|---|---|
| id | UUID primary key |
| email | unique, normalized |
| password_hash | never store raw password |
| full_name | display name |
| is_active | disables login without deleting history |
| created_at | UTC timestamp |

### organizations

| Field | Notes |
|---|---|
| id | UUID primary key |
| name | company or workspace name |
| created_by_user_id | owner who created it |
| created_at | UTC timestamp |

### organization_memberships

| Field | Notes |
|---|---|
| id | UUID primary key |
| organization_id | scoped org |
| user_id | member user |
| role | owner, reviewer, viewer |
| created_at | UTC timestamp |

### documents

| Field | Notes |
|---|---|
| id | UUID primary key |
| organization_id | tenant boundary |
| uploaded_by_user_id | uploader |
| original_filename | sanitized display name |
| stored_filename | generated safe name |
| content_type | detected/validated content type |
| file_size_bytes | validated size |
| sha256_hash | duplicate and integrity check |
| status | pending, approved, rejected, needs_info |
| created_at | UTC timestamp |

### document_facts

| Field | Notes |
|---|---|
| id | UUID primary key |
| document_id | linked document |
| vendor_name | fake/sample vendor |
| invoice_number | optional but useful |
| invoice_date | optional |
| due_date | optional |
| amount_cents | integer cents |
| currency | default USD |
| category | simple accounting category |
| memo | optional note |

### control_flags

| Field | Notes |
|---|---|
| id | UUID primary key |
| document_id | linked document |
| flag_type | missing_vendor, duplicate_invoice, etc. |
| severity | info, warning, blocker |
| reason | plain-English reason |
| created_at | UTC timestamp |

### review_decisions

| Field | Notes |
|---|---|
| id | UUID primary key |
| document_id | linked document |
| reviewer_user_id | decision maker |
| decision | approved, rejected, needs_info |
| reason | required explanation |
| created_at | UTC timestamp |

### audit_entries

| Field | Notes |
|---|---|
| id | UUID primary key |
| organization_id | scoped org, nullable for account-level events |
| actor_user_id | user who acted, nullable for system actions |
| action | short action name |
| entity_type | document, organization, user, export |
| entity_id | affected entity |
| summary | human-readable summary |
| metadata_json | structured details |
| created_at | UTC timestamp |

## Authorization model

Vault is multi-organization from the start.

Every organization-scoped query must filter by `organization_id`. Users must not access documents, reviews, exports, or audit entries from organizations where they are not members.

Role permissions:

| Role | Can upload | Can review | Can export | Can manage members |
|---|---:|---:|---:|---:|
| owner | yes | yes | yes | yes |
| reviewer | yes | yes | yes | no |
| viewer | no | no | yes/read-only | no |

## Security rules

- Store passwords only as salted hashes.
- Do not commit secrets.
- Use `.env.example` for required settings.
- Validate upload size before storing.
- Validate extension and detected content type.
- Generate stored filenames; do not trust user filenames.
- Store files outside the source tree.
- Enforce organization scoping in service functions.
- Keep audit entries append-only through normal application services.
- Avoid raw SQL unless necessary.
- If raw SQL is used, parameterize values and allowlist identifiers.

## Audit rule

If a service changes important state, it must write an audit entry in the same database transaction.

Examples:

- user registered
- organization created
- member invited or role changed
- document uploaded
- document facts parsed
- control flags generated
- document approved
- document rejected
- export generated

## Export design

Vault should export only fake/sample approved records for the repo examples.

Planned exports:

```text
examples/sample_output/approved_documents.csv
examples/sample_output/exceptions_report.csv
examples/sample_output/audit_log.csv
```

Export builders should return plain rows/data structures before writing files. This keeps them easy to test.

## Testing strategy

Tests should cover:

- model validation,
- password hashing behavior,
- auth-protected routes,
- role-based access control,
- organization scoping,
- upload validation,
- duplicate detection,
- status transitions,
- audit logging,
- CSV export output,
- and error handling.

Security-sensitive tests should prove users cannot access another organization's documents.

## Accepted tradeoffs for MVP

- Local file storage instead of S3.
- Structured sample invoice data instead of OCR.
- FastAPI docs as the first UI instead of React.
- Docker Compose for local development only.
- Fake data only.
