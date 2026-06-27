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

Current step: Step 39 — CI, README quickstart, and final hardening.

Status: Complete with documented environment limitations.

MVP status: Complete after local validation.

Approximate project completion: 100%.

Current summary:

* Vault has an initial `src/` Python package layout.
* Tooling is configured in `pyproject.toml` for pytest, Ruff, and mypy.
* Runtime dependencies include FastAPI, SQLAlchemy, psycopg, Alembic,
  argon2-cffi, and python-multipart.
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
  authentication attempts, organization validation failures, document
  metadata validation failures, safe document-not-found behavior, document
  fact validation failures, safe document-fact-not-found behavior, control
  flag validation failures, safe control-flag-not-found behavior, audit
  entry validation failures, and safe audit-entry-not-found behavior.
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
* `POST /organizations/{organization_id}/documents/upload` exists and returns
  HTTP 201 on successful authenticated document upload.
* The document upload route requires a valid bearer token for an active user.
* The document upload route requires organization membership through the
  reusable organization RBAC dependency.
* The document upload route explicitly allows owners and reviewers.
* The document upload route rejects viewers, non-members, and unknown
  organizations with HTTP 403.
* The document upload route rejects missing, invalid, expired, unknown-user,
  and inactive-user bearer tokens with HTTP 401.
* The document upload route accepts one multipart file field named `file`.
* The document upload route validates upload filename, content type, and file
  size using the framework-independent validation helpers.
* The document upload route stores bytes using Vault-generated stored filenames
  and the local storage helper.
* The document upload route creates document metadata through the document
  metadata service.
* The document upload route commits after storage and metadata creation succeed.
* The document upload response returns safe document metadata only.
* The document upload response does not expose local absolute stored paths,
  raw passwords, password hashes, or token internals.
* `POST /organizations/{organization_id}/documents/upload` appears in the
  OpenAPI schema.
* `GET /organizations/{organization_id}/documents` exists and returns safe
  document metadata for one organization.
* `GET /organizations/{organization_id}/documents/{document_id}` exists and
  returns safe metadata for one organization-scoped document.
* Document listing and detail routes require a valid bearer token for an
  active user.
* Document listing and detail routes require organization membership through
  the reusable organization RBAC dependency.
* Document listing and detail routes explicitly allow owners, reviewers, and
  viewers.
* Document listing and detail routes reject non-members and unknown
  organizations with the existing safe HTTP 403 organization-access error.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  continue to return HTTP 401 before document read behavior runs.
* Document listing is scoped to the requested organization.
* Document listing returns newest documents first by `created_at`, with `id`
  as a deterministic tie-breaker.
* Document detail lookup scopes by both `organization_id` and `document_id`.
* Document detail lookup returns HTTP 404 with a safe public message when a
  document is missing or belongs to a different accessible organization.
* Document read responses return safe document metadata only.
* Document read responses do not expose local absolute stored paths, raw
  passwords, password hashes, or token internals.
* `GET /organizations/{organization_id}/documents` appears in the OpenAPI
  schema.
* `GET /organizations/{organization_id}/documents/{document_id}` appears in
  the OpenAPI schema.
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
* `src/vault/documents/validation.py` provides framework-independent upload
  metadata validation helpers.
* `ValidatedUploadMetadata` returns safe display metadata after validation:
  original filename, content type, file size, and normalized extension.
* Upload metadata validation accepts `.csv`, `.txt`, and `.pdf` filenames when
  they match the allowed MVP content types.
* Upload metadata validation rejects blank filenames, whitespace-only
  filenames, path separators, path traversal attempts, hidden filenames,
  extensionless filenames, unsupported extensions, unsupported content types,
  mismatched extension/content-type pairs, zero-byte files, negative file
  sizes, and oversized files.
* Upload metadata validation uses an explicit 5 MiB maximum upload size.
* Upload metadata validation trims surrounding whitespace from display filename
  metadata only.
* Upload metadata validation performs no file reads, file writes, stored
  filename generation, SHA-256 hash calculation, file-content inspection,
  database access, or framework-specific request handling.
* `src/vault/documents/storage.py` provides framework-independent local
  file storage and SHA-256 hashing helpers.
* `StoredUpload` returns stored filename, stored path, file size, and
  SHA-256 hash after bytes are written.
* `calculate_sha256()` returns lowercase hexadecimal SHA-256 hashes for
  upload bytes.
* `generate_stored_filename()` creates Vault-controlled filenames using a
  random UUID-style value and the validated extension.
* Stored filenames preserve only supported validated extensions: `.csv`,
  `.txt`, and `.pdf`.
* Stored filenames do not include original user-provided filename text.
* Stored filenames reject unsupported and malformed extensions.
* `store_upload_bytes()` creates the supplied upload directory when
  missing, writes bytes with exclusive file creation, and returns storage
  metadata.
* Upload byte storage rejects empty bytes and files larger than the same
  5 MiB maximum used by upload metadata validation.
* Upload byte storage writes only under the supplied upload directory and
  fails safely if a generated target filename already exists.
* Upload storage performs no database access, FastAPI request handling,
  document metadata creation, duplicate detection, or audit logging by itself.
* `src/vault/documents/schemas.py` defines safe document response schemas for
  document metadata.
* `src/vault/api/routes/documents.py` provides the organization-scoped
  document upload, listing, and detail API routes.
* `src/vault/documents/models.py` defines the initial `DocumentFact` ORM model.
* The `DocumentFact` model includes `id`, `document_id`, `vendor_name`,
  `invoice_number`, `invoice_date`, `due_date`, `amount_cents`, `currency`,
  `category`, `memo`, and `created_at`.
* Document fact IDs use UUID primary keys.
* Document fact timestamps use the same UTC-aware application-side timestamp
  default as the existing user, organization, membership, and document models.
* Document facts are connected to documents through a foreign key from
  `document_facts.document_id` to `documents.id`.
* Document fact metadata requires `document_id`, `vendor_name`,
  `amount_cents`, `currency`, `category`, and `created_at`.
* Document fact metadata allows nullable `invoice_number`, `invoice_date`,
  `due_date`, and `memo`.
* Document fact metadata uses reasonable string lengths for vendor name,
  invoice number, currency, category, and memo.
* Document fact currency defaults to `USD` at the model level.
* Document fact metadata includes a positive amount check constraint.
* Document fact metadata includes an uppercase three-letter currency check
  constraint.
* Document fact lookup indexes exist for document ID, vendor name, and invoice
  number.
* Document fact duplicate-detection groundwork exists as a non-unique composite
  index on vendor name, invoice number, and amount cents.
* Duplicate document facts are still allowed because duplicate detection has not
  been implemented yet.
* Shared SQLAlchemy model metadata imports `DocumentFact`, so Alembic target
  metadata includes the `document_facts` table.
* A create-document-facts migration exists at
  `alembic/versions/0005_create_document_facts.py`.
* The create-document-facts migration creates only the `document_facts` table
  and its supporting indexes.
* The create-document-facts migration downgrade drops only the
  `document_facts` table after dropping its supporting indexes.
* `src/vault/documents/schemas.py` defines safe request and response schemas for
  document fact creation and fact metadata responses.
* `src/vault/api/routes/documents.py` provides organization-scoped document fact
  create, list, and detail API routes.
* `POST /organizations/{organization_id}/documents/{document_id}/facts` exists
  and returns HTTP 201 on successful fact creation.
* `GET /organizations/{organization_id}/documents/{document_id}/facts` exists
  and returns safe fact metadata for one organization-scoped document.
* `GET /organizations/{organization_id}/documents/{document_id}/facts/{fact_id}`
  exists and returns safe metadata for one organization-scoped document fact.
* Document fact API routes require a valid bearer token for an active user.
* Document fact API routes require organization membership through the reusable
  organization RBAC dependency.
* Document fact creation explicitly allows owners and reviewers.
* Document fact creation rejects viewers, non-members, and unknown organizations.
* Document fact list and detail routes explicitly allow owners, reviewers, and
  viewers.
* Document fact list and detail routes reject non-members and unknown
  organizations with the existing safe HTTP 403 organization-access behavior.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  continue to return HTTP 401 before fact route behavior runs.
* Fact routes verify the path document belongs to the path organization before
  creating, listing, or reading facts.
* Documents from another organization are not accepted through fact routes, even
  when the document ID exists.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Fact creation calls the Step 22 `create_document_fact()` service.
* Fact listing calls the Step 22 `list_document_facts()` service.
* Fact detail calls the Step 22 `require_document_fact()` service.
* Successful fact creation commits and refreshes the created fact before
  returning.
* Fact validation errors return HTTP 400 with safe public messages.
* Missing fact detail returns HTTP 404 with a safe public message.
* Fact responses include safe fact metadata only and do not include local
  absolute file paths, raw passwords, password hashes, or token internals.
* Duplicate document facts are still allowed because duplicate detection has not
  been implemented yet.
* `src/vault/documents/service.py` provides typed document facts service
  behavior.
* `create_document_fact()` creates one structured `DocumentFact` record for a
  supplied document ID.
* Document fact creation stores vendor name, optional invoice number, optional
  invoice date, optional due date, amount cents, currency, category, and
  optional memo.
* Document fact creation trims simple metadata string fields.
* Optional blank or whitespace-only invoice numbers and memos are converted to
  `None`.
* Currency is normalized to uppercase before storage.
* Document fact creation rejects blank vendor names, blank currencies, malformed
  currencies, blank categories, and non-positive amounts.
* Currency must be exactly three letters after normalization.
* Document fact records are added to the supplied session and flushed so
  generated IDs are available.
* Document fact creation does not commit automatically.
* Duplicate document facts are still allowed because duplicate detection has not
  been implemented yet.
* Document fact creation does not update document status.
* Document fact creation does not create control flags.
* Document fact creation does not verify organization membership; route-level
  organization access remains deferred to the future document facts API route.
* `list_document_facts()` returns only facts for the requested document.
* Document fact listing is deterministic, oldest first by `created_at`, with
  `id` as a tie-breaker.
* `get_document_fact()` scopes lookup by both `document_id` and `fact_id`.
* `require_document_fact()` raises a safe custom exception when a scoped fact is
  missing.
* Facts from another document are not returned by scoped lookup.
* Upload API tests use temporary upload directories and dependency-overridden
  database sessions, so they do not require Docker, PostgreSQL, network ports,
  real credentials, or private environment variables.
* If storage succeeds but the database commit later fails, Step 19 does not yet
  delete the stored file as rollback cleanup; that cleanup is deferred rather
  than making this route step larger.
* `src/vault/controls/severities.py` defines official control flag severity
  values: `info`, `warning`, and `blocker`.
* `src/vault/controls/types.py` defines the initial official control flag
  type values: `missing_invoice_number`, `missing_invoice_date`,
  `missing_due_date`, `non_usd_currency`, `high_amount`,
  `duplicate_file_hash`, and `duplicate_invoice_attributes`.
* `src/vault/controls/models.py` defines the initial `ControlFlag` ORM model.
* The `ControlFlag` model includes `id`, `document_id`, `flag_type`,
  `severity`, `reason`, and `created_at`.
* Control flag IDs use UUID primary keys.
* Control flag timestamps use the same UTC-aware application-side timestamp
  default as existing user, organization, document, and fact models.
* Control flags are connected to documents through a foreign key from
  `control_flags.document_id` to `documents.id`.
* Control flag metadata requires `document_id`, `flag_type`, `severity`,
  `reason`, and `created_at`.
* Control flag metadata uses reasonable string lengths for flag type,
  severity, and reason.
* Control flag metadata includes a severity check constraint for the official
  severity values.
* Control flag metadata includes a flag type check constraint for the initial
  official flag type values.
* Control flag lookup indexes exist for document ID, severity, and flag type.
* Control flag review-queue groundwork exists as a non-unique composite index
  on document ID and severity.
* Duplicate control flags are still allowed because generation and
  deduplication behavior has not been implemented yet.
* `src/vault/controls/service.py` provides typed control flag service
  behavior.
* `create_control_flag()` creates one `ControlFlag` record for a supplied
  document ID.
* Control flag creation stores document ID, flag type, severity, reason,
  and generated metadata.
* Control flag creation trims flag type, severity, and reason.
* Control flag creation rejects blank flag type, blank severity, and blank
  reason.
* Control flag creation rejects unsupported flag types using the official
  Step 24 type values.
* Control flag creation rejects unsupported severities using the official
  Step 24 severity values.
* Control flag records are added to the supplied session and flushed so
  generated IDs are available.
* Control flag creation does not commit automatically.
* Duplicate control flags are still allowed because duplicate rejection has
  not been implemented yet.
* `list_control_flags()` returns only flags for the requested document.
* Control flag listing is deterministic: blocker before warning before
  info, then oldest first by `created_at`, then by `id`.
* `get_control_flag()` scopes lookup by both document ID and flag ID.
* `require_control_flag()` raises a safe custom exception when a scoped
  control flag is missing.
* Flags from another document are not returned by scoped lookup.
* `generate_control_flags_for_document()` inspects structured document
  facts for one requested document only.
* Initial control flag generation creates warning flags for missing invoice
  numbers and missing invoice dates.
* Initial control flag generation creates info flags for missing due dates.
* Initial control flag generation creates warning flags for non-USD
  currency.
* Initial control flag generation creates blocker flags for amounts greater
  than or equal to 100,000 cents.
* Generated control flag reasons are human-readable and explain why the
  flag exists.
* Control flag generation returns the created `ControlFlag` records and
  flushes them so IDs are available.
* Control flag generation does not commit automatically.
* Control flag generation creates no flags when the requested document has
  no facts.
* Control flag generation creates no flags for clean facts.
* Control flag generation does not create duplicate-file-hash or
  duplicate-invoice-attributes flags yet; duplicate-oriented generation is
  handled by the separate Step 27 duplicate detection helper.
* `find_duplicate_documents_by_hash()` finds same-organization documents with
  the same SHA-256 hash and excludes the target document.
* Duplicate file-hash lookup returns an empty list for missing target documents
  and for no-match cases.
* Duplicate file-hash lookup does not return documents from other organizations.
* `find_duplicate_invoice_facts()` finds same-organization facts from other
  documents with matching vendor name, invoice number, and amount cents.
* Duplicate invoice lookup ignores missing or blank invoice numbers.
* Duplicate invoice lookup compares vendor names case-insensitively.
* Duplicate invoice lookup does not return facts from the same document.
* Duplicate invoice lookup does not return facts from other organizations.
* `generate_duplicate_control_flags_for_document()` creates duplicate-oriented
  control flags for one requested document.
* Duplicate file-hash generation creates a `duplicate_file_hash` flag with
  blocker severity.
* Duplicate invoice-attribute generation creates a
  `duplicate_invoice_attributes` flag with warning severity.
* Generated duplicate reasons mention the duplicate basis: file hash or
  vendor/invoice/amount.
* Generated duplicate reasons do not expose local absolute stored paths.
* Duplicate control flag generation returns the created flags and flushes so IDs
  are available.
* Duplicate control flag generation does not commit automatically.
* Duplicate control flag generation creates no flags when no duplicates exist.
* Duplicate control flag generation does not inspect or flag cross-organization
  duplicates.
* Duplicate control flag generation does not update document status.
* Duplicate duplicate-detection flags may still be generated if the helper is
  called repeatedly; deduplication is deferred to a later step.
* Duplicate detection service behavior does not verify organization membership;
  future route dependencies will own organization access.
* Control flag generation does not update document status.
* Control flag generation does not verify organization membership; route
  dependencies will continue to own organization access in future API
  steps.
* Shared SQLAlchemy model metadata imports `ControlFlag`, so Alembic target
  metadata includes the `control_flags` table.
* A create-control-flags migration exists at
  `alembic/versions/0006_create_control_flags.py`.
* The create-control-flags migration creates only the `control_flags` table and
  its supporting indexes.
* The create-control-flags migration downgrade drops only the
  `control_flags` table after dropping its supporting indexes.
* `src/vault/controls/schemas.py` defines safe control flag response metadata.
* Control flag API responses include `id`, `document_id`, `flag_type`,
  `severity`, `reason`, and `created_at`.
* Control flag API responses do not include local absolute file paths, raw
  passwords, password hashes, or token internals.
* `POST /organizations/{organization_id}/documents/{document_id}/control-flags/generate`
  exists and returns HTTP 200 with a list of generated flags.
* Control flag generation returns an empty list with HTTP 200 when no flags are
  generated.
* `GET /organizations/{organization_id}/documents/{document_id}/control-flags`
  exists and returns safe control flag metadata for one organization-scoped
  document.
* `GET /organizations/{organization_id}/documents/{document_id}/control-flags/{flag_id}`
  exists and returns safe metadata for one organization-scoped control flag.
* Control flag API routes require a valid bearer token for an active user.
* Control flag API routes require organization membership through the reusable
  organization RBAC dependency.
* Control flag generation explicitly allows owners and reviewers.
* Control flag generation rejects viewers, non-members, and unknown
  organizations.
* Control flag list and detail routes explicitly allow owners, reviewers, and
  viewers.
* Control flag list and detail routes reject non-members and unknown
  organizations with the existing safe HTTP 403 organization-access behavior.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  continue to return HTTP 401 before control flag route behavior runs.
* Control flag routes verify the path document belongs to the path organization
  before generating, listing, or reading control flags.
* Documents from another organization are not accepted through control flag
  routes, even when the document ID exists.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Control flag generation calls `generate_control_flags_for_document()`.
* Control flag listing calls `list_control_flags()`.
* Control flag detail calls `require_control_flag()`.
* Successful control flag generation commits and refreshes generated flags
  before returning.
* Control flag detail lookup is scoped by both document ID and flag ID.
* Missing control flag detail returns HTTP 404 with a safe public message.
* Flags from other documents or organizations are not leaked through list or
  detail routes.
* `POST /organizations/{organization_id}/documents/{document_id}/duplicates/generate`
  exists and returns HTTP 200 with a list of generated duplicate-oriented
  control flags.
* Duplicate detection generation returns an empty list with HTTP 200 when no
  duplicate flags are generated.
* Duplicate detection generation requires a valid bearer token for an active
  user.
* Duplicate detection generation requires organization membership through the
  reusable organization RBAC dependency.
* Duplicate detection generation explicitly allows owners and reviewers.
* Duplicate detection generation rejects viewers, non-members, and unknown
  organizations.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  continue to return HTTP 401 before duplicate generation runs.
* Duplicate detection generation verifies the path document belongs to the path
  organization before generating flags.
* Documents from another organization are not accepted through the duplicate
  detection route, even when the document ID exists.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Duplicate detection generation calls
  `generate_duplicate_control_flags_for_document()`.
* Successful duplicate detection generation commits and refreshes generated
  flags before returning.
* Duplicate detection responses include safe control flag metadata only.
* Duplicate detection responses do not expose local absolute stored paths, raw
  passwords, password hashes, or token internals.
* Duplicate detection responses include `duplicate_file_hash` blocker flags
  when same-organization file hash duplicates exist.
* Duplicate detection responses include `duplicate_invoice_attributes` warning
  flags when same-organization invoice attribute duplicates exist.
* Duplicate detection generation does not flag cross-organization file hash or
  invoice attribute duplicates.
* `src/vault/reviews/decisions.py` defines official review decision values:
  `approved`, `rejected`, and `needs_info`.
* `pending` is not an official review decision value.
* `src/vault/reviews/models.py` defines the initial `ReviewDecision` ORM model.
* The `ReviewDecision` model includes `id`, `document_id`,
  `reviewer_user_id`, `decision`, `reason`, and `created_at`.
* Review decision IDs use UUID primary keys.
* Review decision timestamps use the same UTC-aware application-side timestamp
  default as existing user, organization, document, fact, and control models.
* Review decisions are connected to documents through a foreign key from
  `review_decisions.document_id` to `documents.id`.
* Review decisions are connected to reviewers through a foreign key from
  `review_decisions.reviewer_user_id` to `users.id`.
* Review decision metadata requires `document_id`, `reviewer_user_id`,
  `decision`, `reason`, and `created_at`.
* Review decision metadata uses reasonable string lengths for decision and
  reason.
* Review decision metadata includes a check constraint for the official review
  decision values.
* Review decision lookup indexes exist for document ID, reviewer user ID, and
  decision.
* Review decision history-query groundwork exists as a non-unique composite
  index on document ID and created-at timestamp.
* Multiple review decisions for the same document remain allowed because review
  history may matter later.
* Shared SQLAlchemy model metadata imports `ReviewDecision`, so Alembic target
  metadata includes the `review_decisions` table.
* A create-review-decisions migration exists at
  `alembic/versions/0007_create_review_decisions.py`.
* The create-review-decisions migration creates only the `review_decisions`
  table and its supporting indexes.
* The create-review-decisions migration downgrade drops only the
  `review_decisions` table after dropping its supporting indexes.
* `src/vault/reviews/service.py` provides typed review decision service
  behavior.
* `create_review_decision()` creates one `ReviewDecision` record for a supplied
  document ID.
* Review decision creation loads the linked document by ID before writing the
  decision.
* Missing target documents raise a safe custom review not-found exception.
* Review decision creation stores document ID, reviewer user ID, decision,
  reason, and generated metadata.
* Review decision creation trims decision and reason values.
* Review decision creation rejects blank decisions, blank reasons,
  whitespace-only reasons, unsupported decisions, and `pending` decisions.
* A reason is required for approved, rejected, and needs-info decisions.
* Review decision records are added to the supplied session and flushed so IDs
  are available.
* Review decision creation does not commit automatically.
* Review decision creation updates the linked document status: `approved` maps
  to `approved`, `rejected` maps to `rejected`, and `needs_info` maps to
  `needs_info`.
* Multiple review decisions for the same document remain allowed.
* Later review decisions can update the document status again.
* `list_review_decisions()` returns only review decisions for the requested
  document.
* Review decision listing is deterministic, oldest first by `created_at`, with
  `id` as a tie-breaker.
* `get_review_decision()` scopes lookup by both document ID and review decision
  ID.
* `require_review_decision()` raises a safe custom exception when a scoped
  review decision is missing.
* Review decisions from another document are not returned by scoped lookup.
* Review decision service behavior does not verify organization membership;
  future route dependencies will own organization access.
* Review decision service behavior itself does not write audit entries; Step 34
  route wiring writes audit entries in the same session as the API workflow.
* `src/vault/reviews/schemas.py` defines safe request and response schemas for
  review decision APIs.
* Review decision creation requests include `decision` and `reason`.
* Review decision API responses include safe metadata only: `id`, `document_id`,
  `reviewer_user_id`, `decision`, `reason`, and `created_at`.
* Review decision API responses do not include local absolute stored paths, raw
  passwords, password hashes, or token internals.
* `POST /organizations/{organization_id}/documents/{document_id}/review` exists
  and returns HTTP 201 on successful review decision creation.
* `GET /organizations/{organization_id}/documents/{document_id}/reviews` exists
  and returns safe review decision metadata for one organization-scoped
  document.
* `GET /organizations/{organization_id}/documents/{document_id}/reviews/{review_decision_id}`
  exists and returns safe metadata for one document-scoped review decision.
* Review decision API routes require a valid bearer token for an active user.
* Review decision API routes require organization membership through the
  reusable organization RBAC dependency.
* Review decision creation explicitly allows owners and reviewers.
* Review decision creation rejects viewers, non-members, and unknown
  organizations.
* Review decision list and detail routes explicitly allow owners, reviewers,
  and viewers.
* Review decision list and detail routes reject non-members and unknown
  organizations with the existing safe HTTP 403 organization-access behavior.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  continue to return HTTP 401 before review route behavior runs.
* Review routes verify the path document belongs to the path organization before
  creating, listing, or reading review decisions.
* Documents from another organization are not accepted through review routes,
  even when the document ID exists.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Review creation calls `create_review_decision()`.
* Review listing calls `list_review_decisions()`.
* Review detail calls `require_review_decision()`.
* Successful review creation commits and refreshes the created review decision
  and linked document before returning.
* Review validation errors return HTTP 400 with safe public messages.
* Missing review detail returns HTTP 404 with a safe public message.
* Review detail lookup is scoped by both document ID and review decision ID.
* Review decisions from other documents or organizations are not leaked through
  list or detail routes.
* Multiple review decisions for the same document remain allowed through the
  API.
* Later review decisions can update the document status again through the API.
* Review decision API routes write safe audit entries for review decisions and
  actual document status changes.
* `src/vault/audit/actions.py` defines official audit action values:
  `user_registered`, `organization_created`, `document_uploaded`,
  `document_fact_created`, `control_flags_generated`,
  `duplicate_flags_generated`, `review_decision_created`,
  `document_status_changed`, and `export_generated`.
* `src/vault/audit/entities.py` defines official audit entity type values:
  `user`, `organization`, `document`, `document_fact`, `control_flag`,
  `review_decision`, and `export`.
* `src/vault/audit/models.py` defines the initial `AuditEntry` ORM model.
* The `AuditEntry` model includes `id`, `organization_id`,
  `actor_user_id`, `action`, `entity_type`, `entity_id`, `summary`,
  `metadata_json`, and `created_at`.
* Audit entry IDs use UUID primary keys.
* Audit entry timestamps use the same UTC-aware application-side timestamp
  default as existing user, organization, document, fact, control, and review
  models.
* Audit entries can optionally link to organizations through a nullable
  foreign key from `audit_entries.organization_id` to `organizations.id`.
* Audit entries can optionally link to actor users through a nullable foreign
  key from `audit_entries.actor_user_id` to `users.id`.
* `entity_id` is nullable and intentionally has no foreign key because the
  paired `entity_type` can refer to multiple tables.
* Audit entry metadata requires `action`, `entity_type`, `summary`,
  `metadata_json`, and `created_at`.
* Audit entry metadata uses SQLAlchemy `JSON` for `metadata_json` with a safe
  empty-object default.
* Audit entry metadata uses reasonable string lengths for action, entity type,
  and summary.
* Audit entry metadata includes check constraints for official action values
  and official entity type values.
* Audit entry lookup indexes exist for organization ID, actor user ID, action,
  entity type, and created-at timestamp.
* Audit entry future-query indexes exist on organization ID plus created-at and
  entity type plus entity ID.
* Shared SQLAlchemy model metadata imports `AuditEntry`, so Alembic target
  metadata includes the `audit_entries` table.
* A create-audit-entries migration exists at
  `alembic/versions/0008_create_audit_entries.py`.
* The create-audit-entries migration creates only the `audit_entries` table and
  its supporting indexes.
* The create-audit-entries migration downgrade drops only the `audit_entries`
  table after dropping its supporting indexes.
* `src/vault/audit/service.py` provides typed audit entry service behavior.
* `create_audit_entry()` creates one `AuditEntry` record.
* Audit entry creation accepts optional organization ID, optional actor user ID,
  action, entity type, optional entity ID, summary, and optional metadata.
* Audit entry creation trims action, entity type, and summary values.
* Audit entry creation rejects blank action, blank entity type, and blank
  summary values.
* Audit entry creation rejects unsupported action values using the official
  Step 32 action values.
* Audit entry creation rejects unsupported entity type values using the official
  Step 32 entity type values.
* Audit entry creation stores an empty metadata object when metadata is omitted.
* Audit entry creation rejects explicit null metadata and non-object metadata.
* Audit entry creation copies caller-provided metadata into a plain dictionary.
* Audit entry records are added to the supplied session and flushed so IDs are
  available.
* Audit entry creation does not commit automatically.
* Audit entry creation allows nullable organization IDs for future account or
  system events.
* Audit entry creation allows nullable actor user IDs for future system events.
* Audit entry creation allows nullable entity IDs.
* `list_audit_entries()` returns only entries for the requested organization.
* Audit entry organization listing excludes organization-null entries.
* Audit entry organization listing is deterministic, newest first by
  `created_at`, then `id`.
* `list_audit_entries_for_entity()` scopes entries by entity type and entity ID.
* `get_audit_entry()` scopes detail lookup by organization ID and audit entry
  ID.
* `require_audit_entry()` raises a safe custom exception when a scoped audit
  entry is missing.
* Audit entries from other organizations are not returned by organization-
  scoped lookup.
* Organization-null audit entries are not returned through organization-scoped
  detail lookup.
* Audit service behavior does not verify organization membership directly;
  organization access is enforced through route dependencies.
* Audit service listing supports optional action, entity type, and entity ID
  filters while preserving organization scope.
* Audit service tests use safe metadata examples that avoid raw passwords,
  password hashes, bearer tokens, token payloads, and local absolute file paths.
* `src/vault/audit/schemas.py` defines safe audit response metadata.
* Audit API responses include `id`, `organization_id`, `actor_user_id`,
  `action`, `entity_type`, `entity_id`, `summary`, `metadata_json`, and
  `created_at`.
* Audit API response metadata remains structured while redacting risky
  password, password-hash, bearer-token, token-payload, and local absolute
  stored-path values.
* `src/vault/api/routes/audit.py` provides organization-scoped audit list
  and detail API routes.
* `GET /organizations/{organization_id}/audit` exists.
* `GET /organizations/{organization_id}/audit/{audit_entry_id}` exists.
* Audit routes require authentication through the existing current-user
  dependency chain.
* Audit routes require organization membership through the reusable
  organization RBAC dependency.
* Audit list and detail routes explicitly allow owners, reviewers, and
  viewers.
* Audit list and detail routes reject non-members and unknown organizations
  with the existing safe HTTP 403 organization-access behavior.
* Audit list calls `list_audit_entries()`.
* Audit detail calls `require_audit_entry()`.
* Audit detail lookup is scoped by both organization ID and audit entry ID.
* Audit routes do not return audit entries from other organizations.
* Audit routes do not return organization-null audit entries.
* Missing audit entry detail returns HTTP 404 with a safe public message.
* Audit read routes do not write audit entries.
* Step 34 wires audit entry creation into the important state-changing API
  workflows.
* Step 35 adds audit API routes without adding exports, sample outputs, CI
  files, migrations, or README final polish.
* Step 36 adds the `src/vault/exports/` package for CSV export builders.
* Approved-documents, exception-report, and audit-log CSV builders return text
  from in-memory buffers and do not write files.
* Export row dataclasses exist for approved documents, exception reports, and
  audit logs.
* Database-backed export row helpers are scoped to one organization.
* Approved-document export rows include approved documents only.
* Approved-document export rows include structured fact fields where present.
* Approved documents without facts are included with blank fact fields.
* Exception-report export rows include same-organization control flags across
  pending, rejected, needs-info, and approved document statuses.
* Exception-report rows order blocker flags before warning flags before info
  flags, then newest flags first.
* Audit-log export rows include same-organization audit entries only.
* Audit-log export rows exclude organization-null audit entries.
* Audit-log metadata is serialized as stable JSON text with deterministic key
  ordering.
* Audit-log export metadata uses safe redaction for raw passwords, password
  hashes, bearer tokens, token payloads, and local absolute stored paths.
* Empty exports return header-only CSV text.
* CSV escaping is delegated to the Python standard-library `csv` module.
* `src/vault/api/routes/exports.py` provides organization-scoped CSV export
  routes.
* `GET /organizations/{organization_id}/exports/approved-documents` exists.
* `GET /organizations/{organization_id}/exports/exceptions-report` exists.
* `GET /organizations/{organization_id}/exports/audit-log` exists.
* Export routes require authentication and organization membership.
* Export routes explicitly allow owners and reviewers.
* Export routes reject viewers, non-members, and unknown organizations with
  safe access behavior.
* Export routes return CSV responses with safe attachment filenames.
* Approved-document export responses include approved same-organization
  documents only and include structured fact fields where present.
* Exception-report export responses include same-organization control flags
  only.
* Audit-log export responses include same-organization audit entries only and
  exclude organization-null entries.
* Successful export routes create safe `export_generated` audit entries in the
  same request session before commit.
* Export-generated audit entries use entity type `export`, no entity ID,
  organization scope, actor user ID, export type, filename, and row count.
* Export audit metadata does not include full CSV contents.
* Failed and unauthorized export attempts do not create audit entries.
* Export routes do not write CSV files to disk.
* Step 38 adds fake sample input files under `examples/sample_input/`.
* Step 38 adds fake uploaded text documents under
  `examples/sample_input/uploads/`.
* Step 38 adds `examples/sample_input/invoice_facts.csv` using the official
  sample invoice fact columns.
* Step 38 adds deterministic committed sample output CSV files under
  `examples/sample_output/`.
* Step 38 adds `python scripts/run_vault.py export-demo --output-dir
  examples/sample_output`.
* The demo export command uses deterministic fake in-memory row data and the
  existing CSV builders.
* The demo export command does not require Docker, PostgreSQL, network access,
  environment variables, local databases, or uploaded storage files.
* The demo export command creates the output directory when missing.
* The demo export command overwrites only the official demo output files and
  does not delete unrelated files.
* Committed sample outputs match regenerated demo export output.
* No sample output files, demo seed command, migrations, CI, or README final
  polish were added in Step 37.
* No membership management API routes, document download routes, refresh
  tokens, password reset, email verification, sample outputs, local
  databases beyond metadata migrations, or application container were added.
* Step 39 adds `.github/workflows/ci.yml`.
* Step 39 CI uses `python -m pip_audit --skip-editable` for dependency audit.
* Step 39 updates `README.md`, `docs/Architecture.md`, and
  `docs/Step_Plan.md` to describe implemented behavior honestly.
* Step 39 adds final hardening tests for CI, README, and stale-doc checks.
* Step 39 regenerates deterministic fake sample output CSVs once.
* GitHub Actions CI has been added but has not been observed green in the
  GitHub repository UI from this environment.

Current validation status:

```text
Step 39 validation has now been run locally with one documented upstream
warning and one expected editable-package audit skip.

python -m ruff check .
Passed. All checks passed.

python -m mypy src scripts tests
Passed after test helper return annotations were fixed. Success: no issues
found in 99 source files.

python -m pytest
Passed locally. 855 passed, 1 warning in 84.48 seconds. The warning was an
upstream FastAPI/Starlette TestClient deprecation warning about httpx/httpx2,
not a Vault behavior failure.

python -m bandit -r src
Passed. No issues identified.

python -m pip_audit --skip-editable
Passed. No known vulnerabilities found. The local editable Vault package was
skipped as expected because it is not an auditable third-party dependency.

python scripts/run_vault.py --help
Passed. Help text displayed and includes export-demo.

python scripts/run_vault.py export-demo --output-dir examples/sample_output
Passed. Wrote approved_documents.csv, exceptions_report.csv, and audit_log.csv.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Optional Docker-backed migration smoke check
Passed locally after using the Docker Compose database credentials:
postgresql+psycopg://vault_local:vault_local@localhost:5432/vault_local.
`python -m alembic upgrade head` and `python -m alembic current` worked after
the local database URL matched `docker compose config`.

git status
Pending local review after final documentation edits.

git diff examples/sample_output
Pending local review after final documentation edits.

GitHub Actions CI status
Workflow was added locally. CI has not been observed green in GitHub Actions
yet. Do not claim CI is green until the repository UI shows a passing run.
```

Required validation commands:

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit --skip-editable
git status
```

Validation rule:

> Do not mark a step complete until the required validation commands have been run locally, or until the failure is explicitly documented with the reason.

Next planned step:

```text
Post-MVP maintenance — monitor CI, fix reported issues, and consider optional dashboard polish.
```




### Step 39 — CI, README quickstart, and final hardening

Status: Complete with documented environment limitations.

Goal:

* Finish Vault as a portfolio-ready MVP by adding CI, polishing the README
  quickstart honestly around implemented behavior, running final validation,
  fixing real validation defects, and marking the MVP complete in Project
  State.

Completed work:

* Added `.github/workflows/ci.yml`.
* CI runs on `push` and `pull_request`.
* CI uses Python 3.13.
* CI installs the package with development dependencies.
* CI runs Ruff, mypy, pytest, Bandit, and `pip-audit --skip-editable`.
* CI does not require Docker, PostgreSQL, private environment variables, cloud
  credentials, deployment credentials, or secrets.
* Rewrote `README.md` so it describes the implemented MVP instead of the old
  planning-only state.
* README now includes the problem statement, implemented features, tech stack,
  quickstart, local PostgreSQL setup, validation commands, demo export command,
  sample input/output explanation, API overview, security notes, project
  status, and honest limitations.
* README now documents `python -m pip_audit --skip-editable` so the local
  editable Vault package is skipped while third-party dependencies are audited.
* README now shows the Docker Compose local PostgreSQL URL that matches the
  resolved fake local credentials: `vault_local`, `vault_local`, and
  `vault_local`.
* Project State documents the upstream FastAPI/Starlette TestClient
  deprecation warning as a non-blocking dependency warning rather than a Vault
  behavior failure.
* README documents that Docker Compose is for local PostgreSQL and that most
  tests and demo exports do not require Docker.
* README documents that sample data is fake.
* README does not claim production readiness, real OCR, AI extraction, bank
  integrations, real customer data, cloud deployment, or frontend behavior.
* Updated `docs/Architecture.md` to match the implemented backend MVP.
* Updated `docs/Step_Plan.md` to show completed phases, Step 39 status, and
  post-MVP backlog.
* Added `tests/test_final_project_hardening.py`.
* Final hardening tests check the CI workflow commands, README MVP coverage,
  and materially stale documentation markers.
* Fixed real mypy failures caused by redundant `cast(Response, ...)` calls in
  existing API tests under the active mypy version.
* Regenerated deterministic fake sample output CSVs with the official demo
  export command.
* No product features were added.
* No API routes were added.
* No database models or migrations were added.
* No sample output behavior was intentionally changed.

Files created or edited:

```text
.github/workflows/ci.yml
README.md
docs/Architecture.md
docs/Step_Plan.md
docs/Project_State.md
tests/test_final_project_hardening.py
tests/test_audit_api.py
tests/test_control_flags_api.py
tests/test_document_facts_api.py
tests/test_document_read_api.py
tests/test_document_upload_api.py
tests/test_duplicate_detection_api.py
tests/test_review_decision_api.py
examples/sample_output/approved_documents.csv
examples/sample_output/exceptions_report.csv
examples/sample_output/audit_log.csv
```

Commands run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m pytest tests/test_alembic_config.py tests/test_api_health.py tests/test_audit_api.py tests/test_audit_entry_model.py tests/test_audit_entry_service.py tests/test_auth_login_api.py tests/test_auth_login_service.py tests/test_auth_me_api.py tests/test_auth_registration_api.py tests/test_auth_tokens.py tests/test_config.py tests/test_control_flag_model.py tests/test_control_flag_service.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_current_user_dependency.py tests/test_database_config.py tests/test_demo_export_cli.py tests/test_document_fact_model.py tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py tests/test_document_storage.py tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py tests/test_duplicate_detection_service.py -q
python -m pytest tests/test_export_api.py tests/test_export_builders.py tests/test_final_project_hardening.py -q
python -m pytest tests/test_organization_access_service.py tests/test_organization_create_api.py tests/test_organization_models.py tests/test_organization_rbac_dependency.py tests/test_organization_service.py -q
python -m pytest tests/test_package_import.py tests/test_passwords.py -q
python -m pytest tests/test_review_decision_api.py -q
python -m pytest tests/test_review_decision_model.py tests/test_review_decision_service.py -q
python -m pytest tests/test_upload_validation.py tests/test_user_model.py tests/test_user_service.py -q
python -m bandit -r src
python -m pip_audit --skip-editable
python scripts/run_vault.py --help
python scripts/run_vault.py export-demo --output-dir examples/sample_output
python -m alembic history
docker --version
git status --short
git diff examples/sample_output
```

Validation results:

```text
python -m pip install -e ".[dev]"
Passed. Editable install completed with runtime and development dependencies.

python -m ruff check .
Passed. All checks passed.

python -m mypy src scripts tests
Passed after test helper return annotations were fixed. Success: no issues
found in 99 source files.

python -m pytest
Passed locally. 855 passed, 1 warning in 84.48 seconds. The warning was an
upstream FastAPI/Starlette TestClient deprecation warning about httpx/httpx2,
not a Vault behavior failure.

python -m bandit -r src
Passed. No issues identified.

python -m pip_audit --skip-editable
Passed. No known vulnerabilities found. The local editable Vault package was
skipped as expected because it is not an auditable third-party dependency.

python scripts/run_vault.py --help
Passed. Help text displayed and includes export-demo.

python scripts/run_vault.py export-demo --output-dir examples/sample_output
Passed. Wrote approved_documents.csv, exceptions_report.csv, and audit_log.csv.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Optional Docker-backed migration smoke check
Passed locally after using the Docker Compose database credentials:
postgresql+psycopg://vault_local:vault_local@localhost:5432/vault_local.
`python -m alembic upgrade head` and `python -m alembic current` worked after
the local database URL matched `docker compose config`.

git status --short
Pending local review after final documentation edits.

git diff examples/sample_output
Pending local review after final documentation edits.

GitHub Actions CI
Workflow was added locally. CI has not been observed green in GitHub Actions
yet.
```

Definition of done:

* GitHub Actions CI workflow exists.
* CI workflow runs Ruff.
* CI workflow runs mypy.
* CI workflow runs pytest.
* CI workflow runs Bandit.
* CI workflow runs `pip-audit --skip-editable`.
* README quickstart is current and honest.
* README explains the project, features, tech stack, setup, validation, sample
  data, demo export command, API overview, security notes, and limitations.
* README does not claim unimplemented features.
* Architecture and step docs are not materially stale.
* Demo sample outputs regenerate deterministically.
* Sample outputs remain fake and safe.
* No real data, secrets, tokens, password hashes, local absolute paths, local
  databases, generated upload storage, or PostgreSQL volume data are included.
* Ruff passes.
* Mypy passes.
* Pytest passed locally: 855 passed with one upstream FastAPI/Starlette TestClient deprecation warning.
* Bandit passes.
* pip-audit passed locally with `--skip-editable`; no known vulnerabilities were found and the local editable package was skipped as expected.
* CLI help works.
* Demo export command works.
* Alembic history works.
* Optional Docker-backed migration smoke check passed locally after using the Docker Compose `vault_local` credentials.
* Project State is updated.
* MVP completion status is marked complete with documented limitations.

Suggested commit message:

```text
Add CI and final README polish
```

### Step 38 — Sample input/output and demo export command

Status: Complete with documented environment limitations.

Goal:

* Add fake sample input files, a deterministic local demo export command,
  and committed sample output CSV files so Vault can demonstrate the
  export workflow without real customer data, network services, Docker,
  PostgreSQL, or manual API calls.

Completed work:

* Added fake sample input folder `examples/sample_input/`.
* Added `examples/sample_input/invoice_facts.csv`.
* The fake invoice facts CSV uses the official required columns:
  `vendor_name`, `invoice_number`, `invoice_date`, `amount_cents`,
  `currency`, and `category`.
* The fake invoice facts CSV includes optional `due_date` and `memo`
  columns.
* Added fake uploaded text documents under
  `examples/sample_input/uploads/`.
* Sample upload filenames are safe and simple.
* Sample upload contents are fake text only.
* Added `export-demo` to `scripts/run_vault.py`.
* Required command works:
  `python scripts/run_vault.py export-demo --output-dir examples/sample_output`.
* The demo export command creates deterministic in-memory fake export rows.
* The demo export command calls the existing Step 36 CSV builders directly.
* The demo export command does not require Docker.
* The demo export command does not require PostgreSQL.
* The demo export command does not require network access.
* The demo export command does not require environment variables.
* The demo export command creates the output directory when missing.
* The demo export command overwrites only `approved_documents.csv`,
  `exceptions_report.csv`, and `audit_log.csv`.
* The demo export command does not delete unrelated files in the output
  directory.
* The demo export command prints a short success message listing the files
  it wrote.
* Added committed sample outputs under `examples/sample_output/`.
* Sample approved-documents output includes one approved document with
  structured fact fields and one approved document with blank fact fields.
* Sample exceptions-report output includes one blocker flag and one warning
  flag.
* Sample audit-log output includes several fake audit rows, including an
  `export_generated` row.
* Sample audit metadata avoids raw passwords, password hashes, bearer tokens,
  token payloads, local absolute paths, secrets, and real customer data.
* Added `tests/test_demo_export_cli.py`.
* Tests cover CLI help, successful command execution, missing output
  directory creation, deterministic output, official file overwrite,
  unrelated file preservation, no local databases, no uploaded storage files,
  current headers, representative fake rows, risky output scanning, committed
  output drift, invoice facts columns, fake upload files, and sample-input
  safety checks.
* No API behavior was changed.
* No migrations were added.
* No CI workflow was added.
* README final polish remains deferred to Step 39.

Files created or edited:

```text
scripts/run_vault.py
tests/test_demo_export_cli.py
examples/sample_input/invoice_facts.csv
examples/sample_input/uploads/acme-office-supplies.txt
examples/sample_input/uploads/brightline-consulting.txt
examples/sample_input/uploads/coastal-utilities.txt
examples/sample_output/approved_documents.csv
examples/sample_output/exceptions_report.csv
examples/sample_output/audit_log.csv
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_demo_export_cli.py -q
python -m pytest tests/test_demo_export_cli.py tests/test_export_builders.py -q
python -m pytest -q
python -m py_compile scripts/run_vault.py tests/test_demo_export_cli.py
python scripts/run_vault.py --help
python scripts/run_vault.py export-demo --output-dir examples/sample_output
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
```

Validation results:

```text
python -m pytest tests/test_demo_export_cli.py -q
Passed. 14 passed.

python -m pytest tests/test_demo_export_cli.py tests/test_export_builders.py -q
Passed. 23 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after
a reported test failure. Focused Step 38 coverage passed.

python -m py_compile scripts/run_vault.py tests/test_demo_export_cli.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed and includes export-demo.

python scripts/run_vault.py export-demo --output-dir examples/sample_output
Passed. Wrote approved_documents.csv, exceptions_report.csv, and
audit_log.csv.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Python line-length check for Step 38 edited Python files
Passed. No lines over 88 characters were found.

python -m ruff check .
Could not run in this environment because Ruff is not installed in the
active runtime.

python -m mypy src scripts tests
Could not run in this environment because mypy is not installed in the
active runtime.

python -m bandit -r src
Could not run in this environment because Bandit is not installed in the
active runtime.

python -m pip_audit
Could not run in this environment because pip-audit is not installed in the
active runtime. No project vulnerability result was produced.

git status --short
Did not complete in this environment because the uploaded repo zip did not
include `.git` metadata.

Optional Docker-backed migration smoke check
Skipped in this environment because Docker is not installed.
```

Definition of done:

* Fake sample input folder exists.
* Fake invoice facts CSV exists.
* Fake uploaded document files exist.
* Sample input contains fake data only.
* Demo export command exists.
* Demo export command works without Docker, PostgreSQL, network access, or
  private environment variables.
* Demo export command writes the three official CSV outputs.
* Demo export command writes deterministic output.
* Demo export command does not delete unrelated files.
* Demo export command does not write local databases.
* Demo export command does not write uploaded storage files.
* Committed sample output CSV files exist.
* Committed sample output CSV files match regenerated demo output.
* Sample approved-documents output uses current headers.
* Sample exceptions-report output uses current headers.
* Sample audit-log output uses current headers.
* Sample outputs include representative fake rows.
* Sample outputs contain no raw passwords, password hashes, bearer tokens,
  token payloads, or local absolute paths.
* No API behavior is changed.
* No migrations are added.
* No CI workflow is added yet.
* README final polish is still deferred.
* Focused Step 38 tests pass.
* CLI help works.
* Demo export command works.
* Alembic history works.
* Project State is updated.

Suggested commit message:

```text
Add demo sample exports
```


### Step 37 — Export API routes

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped export API routes that return
  approved documents, exception reports, and audit logs as downloadable CSV
  responses, with safe `export_generated` audit entries for successful exports.

Completed work:

* Added `src/vault/api/routes/exports.py`.
* Included the export router in the FastAPI app factory.
* Added `GET /organizations/{organization_id}/exports/approved-documents`.
* Added `GET /organizations/{organization_id}/exports/exceptions-report`.
* Added `GET /organizations/{organization_id}/exports/audit-log`.
* Export routes require authentication through the existing current-user
  dependency chain.
* Export routes require organization membership through the existing
  `require_organization_roles()` dependency factory.
* Export routes explicitly allow owners and reviewers.
* Export routes reject viewers, non-members, and unknown organizations.
* Missing, invalid, expired, unknown-user, and inactive-user bearer tokens
  return HTTP 401 before export behavior runs.
* Export routes call the Step 36 export row helpers and CSV builders.
* Export routes return in-memory CSV text responses with media type `text/csv`.
* Export routes set safe attachment filenames: `approved_documents.csv`,
  `exceptions_report.csv`, and `audit_log.csv`.
* Approved-documents export includes approved same-organization documents only.
* Approved-documents export excludes pending, rejected, and needs-info
  documents.
* Approved-documents export includes structured fact fields where present.
* Exception-report export includes same-organization control flags only.
* Audit-log export includes same-organization audit entries only.
* Audit-log export excludes organization-null audit entries.
* Empty exports return header-only CSV responses.
* Export responses do not expose raw passwords, password hashes, bearer tokens,
  token payload values, or local absolute stored paths.
* Each successful export creates one `export_generated` audit entry.
* Export-generated audit entries are scoped to the requested organization.
* Export-generated audit entries use the authenticated user as actor.
* Export-generated audit entries use entity type `export` and no entity ID.
* Export-generated audit metadata includes export type, filename, and row count.
* Export-generated audit metadata does not include full CSV contents.
* Unauthorized, non-member, unknown-organization, and viewer-denied attempts do
  not create export audit entries.
* Export routes do not write CSV files to disk.
* Export routes appear in OpenAPI.
* Added `tests/test_export_api.py`.
* Tests cover successful exports, owner/reviewer access, viewer and non-member
  denial, authentication failure, unknown organizations, stable headers, media
  type, attachment filenames, organization scoping, empty exports, safe
  responses, export audit entry creation, no audit on denied attempts, no file
  writes, and OpenAPI inclusion.
* No sample input files, sample output files, demo seed command, demo export
  command, migrations, CI files, README final polish, frontend, dashboard, or
  table changes were added.

Files created or edited:

```text
src/vault/api/main.py
src/vault/api/routes/exports.py
tests/test_export_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_export_api.py -q
python -m pytest tests/test_export_api.py tests/test_export_builders.py -q
python -m pytest -q
python -m py_compile src/vault/api/main.py src/vault/api/routes/exports.py tests/test_export_api.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_export_api.py -q
Passed. 23 passed.

python -m pytest tests/test_export_api.py tests/test_export_builders.py -q
Passed. 32 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. Focused Step 37 coverage passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Python line-length check for Step 37 edited Python files
Passed. No lines over 88 characters were found.

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

Definition of done:

* Export route module exists.
* Export router is included in the FastAPI app.
* Approved-documents export route exists.
* Exceptions-report export route exists.
* Audit-log export route exists.
* Export routes require authentication.
* Export routes require organization membership.
* Owners can generate exports.
* Reviewers can generate exports.
* Viewers cannot generate exports.
* Non-members cannot generate exports.
* Missing, invalid, expired, unknown-user, and inactive-user tokens return
  authentication errors.
* Unknown organizations return safe organization access errors.
* Export routes return `text/csv`.
* Export routes set safe attachment filenames.
* Approved-documents route returns approved-document CSV.
* Exceptions-report route returns exception-report CSV.
* Audit-log route returns audit-log CSV.
* Empty exports return header-only CSV responses.
* Export routes preserve organization boundaries.
* Export responses do not leak another organization's data.
* Export responses do not expose raw passwords, password hashes, bearer tokens,
  token payload values, or local absolute stored paths.
* Successful export routes create safe `export_generated` audit entries.
* Export audit entries use official action and entity type values.
* Export audit entries are scoped to the correct organization.
* Export audit metadata includes export type, filename, and row count.
* Export audit metadata does not include full CSV contents.
* Failed and unauthorized export attempts do not create audit entries.
* Export routes appear in OpenAPI.
* Export routes do not write files to disk.
* No sample input files are added yet.
* No sample output files are generated yet.
* No migrations are added in this step.
* Focused Step 37 tests pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add export API routes
```


### Step 36 — CSV export builders

Status: Complete with documented environment limitations.

Goal:

* Add directly testable CSV export builder functions that produce approved
  documents, exception reports, and audit log CSV text for one organization,
  without adding API routes or writing sample output files yet.

Completed work:

* Added `src/vault/exports/__init__.py`.
* Added `src/vault/exports/schemas.py`.
* Added frozen dataclass row types for approved-document, exception-report,
  and audit-log exports.
* Added `src/vault/exports/builders.py`.
* Added explicit stable header constants for approved-document,
  exception-report, and audit-log CSV exports.
* Added `build_approved_documents_csv()`.
* Added `build_exceptions_report_csv()`.
* Added `build_audit_log_csv()`.
* CSV builders return CSV text only.
* CSV builders use the Python standard-library `csv` module.
* CSV builders use `io.StringIO` for in-memory output.
* CSV builders do not import FastAPI.
* CSV builders do not write files to disk.
* Empty export builders return header-only CSV text.
* CSV builders safely handle commas, quotes, and newlines through the `csv`
  module.
* Audit metadata JSON is serialized with deterministic key ordering and compact
  separators.
* Added `src/vault/exports/service.py`.
* Added organization-scoped approved-document export row query behavior.
* Approved-document export rows include approved documents only.
* Approved-document export rows exclude pending, rejected, and needs-info
  documents.
* Approved-document export rows exclude documents from other organizations.
* Approved-document export rows include structured fact fields where present.
* Approved documents without facts are included with blank fact fields.
* Approved-document rows are ordered newest document first, then by document ID,
  then by oldest fact when multiple facts exist.
* Added organization-scoped exception-report export row query behavior.
* Exception-report rows include control flags for same-organization documents.
* Exception-report rows include document ID, original filename, document status,
  flag ID, flag type, severity, reason, and flag creation timestamp.
* Exception-report rows exclude flags from other organizations.
* Exception-report rows use deterministic severity ordering: blocker, warning,
  info, then newest flag first.
* Added organization-scoped audit-log export row query behavior.
* Audit-log rows include same-organization audit entries only.
* Audit-log rows exclude organization-null audit entries.
* Audit-log rows exclude audit entries from other organizations.
* Added reusable safe audit metadata redaction helper in
  `src/vault/audit/service.py`.
* Audit-log export metadata redacts raw passwords, password hashes, bearer
  tokens, token payloads, and local absolute stored paths.
* Export row queries do not create audit entries yet.
* Added `tests/test_export_builders.py`.
* Tests cover approved-document export headers, status filtering, organization
  scoping, fact fields, blank fact fields, CSV escaping, and empty output.
* Tests cover exception-report headers, flag fields, document status,
  organization scoping, deterministic severity ordering, CSV escaping, and
  empty output.
* Tests cover audit-log headers, organization scoping, organization-null
  exclusion, metadata JSON serialization, deterministic key ordering, redaction,
  CSV escaping, and empty output.
* Tests cover no file writes and no export audit-entry creation.
* No export API routes, download endpoints, sample output files, demo seed
  commands, migrations, CI files, README final polish, or table changes were
  added.

Files created or edited:

```text
src/vault/exports/__init__.py
src/vault/exports/builders.py
src/vault/exports/schemas.py
src/vault/exports/service.py
src/vault/audit/service.py
tests/test_export_builders.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_export_builders.py -q
python -m pytest tests/test_audit_entry_service.py tests/test_export_builders.py -q
python -m pytest -q
python -m py_compile src/vault/exports/__init__.py src/vault/exports/schemas.py src/vault/exports/builders.py src/vault/exports/service.py src/vault/audit/service.py tests/test_export_builders.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_export_builders.py -q
Passed. 9 passed.

python -m pytest tests/test_audit_entry_service.py tests/test_export_builders.py -q
Passed. 58 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. Focused Step 36 coverage passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Python line-length check for Step 36 edited Python files
Passed. No lines over 88 characters were found.

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

Definition of done:

* Exports package exists.
* Approved-documents CSV builder exists.
* Exception-report CSV builder exists.
* Audit-log CSV builder exists.
* Export builders return CSV text.
* Export builders do not write files.
* Approved-documents export is organization-scoped.
* Approved-documents export includes approved documents only.
* Approved-documents export includes stable headers.
* Approved-documents export includes structured fact fields where available.
* Approved documents without facts export with blank fact fields.
* Exception-report export is organization-scoped.
* Exception-report export includes control flags.
* Exception-report export includes stable headers.
* Audit-log export is organization-scoped.
* Audit-log export excludes organization-null entries.
* Audit-log export includes stable headers.
* Audit metadata is serialized safely.
* Audit metadata redaction is preserved.
* Empty exports return headers.
* CSV special characters are handled safely through the `csv` module.
* Export row ordering is deterministic.
* No export API routes are added yet.
* No sample output files are generated yet.
* No export audit entries are written yet.
* No migrations are added in this step.
* Focused Step 36 tests pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add CSV export builders
```


### Step 35 — Audit API route

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped audit API routes that allow
  organization members to list audit entries and read one audit entry detail
  safely, without adding CSV exports yet.

Completed work:

* Added `src/vault/audit/schemas.py`.
* Added `AuditEntryResponse` with safe audit metadata fields.
* Audit responses include `id`, `organization_id`, `actor_user_id`, `action`,
  `entity_type`, `entity_id`, `summary`, `metadata_json`, and `created_at`.
* Audit response metadata remains structured.
* Audit response metadata redacts risky raw-password, password-hash,
  bearer-token, token-payload, and local absolute stored-path values.
* Added `src/vault/api/routes/audit.py`.
* Included the audit router in the FastAPI app factory.
* Added `GET /organizations/{organization_id}/audit`.
* Added `GET /organizations/{organization_id}/audit/{audit_entry_id}`.
* Audit routes require authentication through the existing current-user
  dependency chain.
* Audit routes require organization membership through the existing
  `require_organization_roles()` dependency factory.
* Audit list and detail explicitly allow owners, reviewers, and viewers.
* Non-members cannot list or read audit entries.
* Unknown organizations continue to return the existing safe HTTP 403
  organization-access behavior.
* Missing, invalid, expired, and inactive-user tokens continue to return
  HTTP 401 before audit route behavior runs.
* Audit listing calls `list_audit_entries()`.
* Audit detail calls `require_audit_entry()`.
* Audit detail lookup scopes by both organization ID and audit entry ID.
* Audit entries from another organization are not returned.
* Organization-null audit entries are not returned through organization-scoped
  audit routes.
* Missing audit entry detail returns HTTP 404 with a safe public message.
* Audit list responses use deterministic service ordering, newest first by
  `created_at`, then `id`.
* Added optional audit list filters for `action`, `entity_type`, and
  `entity_id`.
* Audit filters remain organization-scoped.
* Unsupported action and entity type filters return HTTP 400 with safe
  messages.
* Audit read routes do not write audit entries.
* No CSV exports, approved-document export route, exception export route, audit
  log export route, sample input/output generation, demo seed command, CI,
  README final polish, migrations, or table changes were added.

Files created or edited:

```text
src/vault/api/main.py
src/vault/api/routes/audit.py
src/vault/audit/schemas.py
src/vault/audit/service.py
tests/test_audit_api.py
tests/test_audit_entry_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_audit_api.py -q
python -m pytest tests/test_audit_entry_service.py -q
python -m pytest tests/test_audit_api.py tests/test_audit_entry_service.py -q
python -m pytest -q
python -m py_compile src/vault/api/main.py src/vault/api/routes/audit.py src/vault/audit/schemas.py src/vault/audit/service.py tests/test_audit_api.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_audit_api.py -q
Passed. 42 passed.

python -m pytest tests/test_audit_entry_service.py -q
Passed. 49 passed.

python -m pytest tests/test_audit_api.py tests/test_audit_entry_service.py -q
Passed. 91 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. Focused Step 35 coverage passed.

python -m py_compile ...
Passed.

Python line-length check for Step 35 edited Python files
Passed. No lines over 88 characters were found.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

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

Definition of done:

* Audit response schema exists.
* Audit route module exists.
* Audit router is included in the FastAPI app.
* `GET /organizations/{organization_id}/audit` exists.
* `GET /organizations/{organization_id}/audit/{audit_entry_id}` exists.
* Audit routes require authentication.
* Audit routes require organization membership.
* Owners can list and read audit entries.
* Reviewers can list and read audit entries.
* Viewers can list and read audit entries.
* Non-members cannot list or read audit entries.
* Missing, invalid, expired, and inactive-user tokens return authentication
  errors.
* Unknown organizations return safe organization access errors.
* Audit listing is scoped to the requested organization.
* Audit listing does not leak another organization's entries.
* Audit listing excludes organization-null entries.
* Audit detail lookup is scoped by organization ID and audit entry ID.
* Audit detail does not leak another organization's entries.
* Audit detail does not return organization-null entries.
* Missing audit detail returns safe not-found behavior.
* Audit responses return safe audit metadata.
* Audit responses do not expose raw passwords.
* Audit responses do not expose password hashes.
* Audit responses do not expose bearer tokens.
* Audit responses do not expose token payloads.
* Audit responses do not expose local absolute stored paths.
* Audit read routes do not create audit entries.
* Routes appear in OpenAPI.
* No exports are added yet.
* No sample outputs are added yet.
* No migrations are added in this step.
* Tests cover successful list/detail, role behavior, auth failure,
  organization scoping, safe responses, no audit-on-read behavior, OpenAPI,
  and filter behavior.
* Focused Step 35 tests pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add audit API routes
```


### Step 34 — Wire audit entries into state-changing services

Status: Complete with documented environment limitations.

Goal:

* Wire safe audit entry creation into important state-changing API workflows
  using the existing Step 33 `create_audit_entry()` service, without adding
  audit API routes, export routes, sample outputs, migrations, CI, or README
  final polish.

Completed work:

* Wired `POST /auth/register` to create a `user_registered` audit entry.
* Registration audit entries use entity type `user` and entity ID equal to the
  created user ID.
* Registration audit entries use the created user as actor; this is documented
  in safe metadata with `actor_user_id_policy` set to `created_user`.
* Registration audit metadata includes safe public user fields only and does
  not include raw passwords, password hashes, bearer tokens, or token payloads.
* Wired `POST /organizations` to create an `organization_created` audit entry.
* Organization creation audit entries are scoped to the created organization.
* Organization creation audit metadata includes safe organization ID, name,
  creator user ID, and owner membership ID.
* Wired `POST /organizations/{organization_id}/documents/upload` to create a
  `document_uploaded` audit entry.
* Document upload audit metadata includes document ID, original filename,
  content type, file size, SHA-256 hash, and document status.
* Document upload audit metadata does not include the local absolute stored
  file path.
* Wired `POST /organizations/{organization_id}/documents/{document_id}/facts`
  to create a `document_fact_created` audit entry.
* Document fact audit metadata includes document ID, vendor name, invoice
  number, amount cents, currency, and category.
* Wired control flag generation to create `control_flags_generated` audit
  entries.
* Control flag generation audit metadata includes document ID, generated flag
  count, and generated flag IDs, types, and severities.
* Control flag generation now writes an audit entry even when zero flags are
  generated.
* Wired duplicate flag generation to create `duplicate_flags_generated` audit
  entries.
* Duplicate flag generation audit metadata includes document ID, generated
  duplicate flag count, and generated flag IDs, types, and severities.
* Duplicate flag generation now writes an audit entry even when zero duplicate
  flags are generated.
* Wired review decision creation to create `review_decision_created` audit
  entries.
* Review decision audit metadata includes document ID, decision, reason, and
  resulting document status.
* Review decision creation now creates a `document_status_changed` audit entry
  only when the document status actually changes.
* Status-change audit metadata includes document ID, old status, and new
  status.
* Audit entries are added to the same SQLAlchemy session before the successful
  route commit.
* Failed validation attempts do not create audit entries in this step.
* Unauthorized requests do not create audit entries.
* Viewer-denied state changes do not create audit entries.
* Audit entries use official Step 32 action values.
* Audit entries use official Step 32 entity type values.
* No new audit action values were added.
* No new audit entity type values were added.
* No database migrations were added.
* No audit API routes, audit exports, approved-document exports, exception
  exports, sample outputs, CI, or README final polish were added.

Files created or edited:

```text
src/vault/api/routes/auth.py
src/vault/api/routes/organizations.py
src/vault/api/routes/documents.py
tests/test_auth_registration_api.py
tests/test_organization_create_api.py
tests/test_document_upload_api.py
tests/test_document_facts_api.py
tests/test_control_flags_api.py
tests/test_duplicate_detection_api.py
tests/test_review_decision_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_auth_registration_api.py -q
python -m pytest tests/test_organization_create_api.py -q
python -m pytest tests/test_document_upload_api.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_duplicate_detection_api.py -q
python -m pytest tests/test_review_decision_api.py -q
python -m pytest tests/test_auth_registration_api.py tests/test_organization_create_api.py tests/test_document_upload_api.py -q
python -m pytest tests/test_document_facts_api.py tests/test_control_flags_api.py -q
python -m pytest tests/test_duplicate_detection_api.py tests/test_review_decision_api.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py tests/test_audit_entry_model.py tests/test_audit_entry_service.py tests/test_auth_login_api.py tests/test_auth_login_service.py tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py tests/test_control_flag_model.py tests/test_control_flag_service.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_database_config.py tests/test_document_fact_model.py tests/test_document_fact_service.py tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py tests/test_document_service.py tests/test_document_storage.py tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py tests/test_duplicate_detection_service.py tests/test_organization_access_service.py tests/test_organization_create_api.py -q
python -m pytest tests/test_organization_models.py tests/test_organization_rbac_dependency.py tests/test_organization_service.py tests/test_package_import.py tests/test_passwords.py -q
python -m pytest tests/test_review_decision_api.py tests/test_review_decision_model.py tests/test_review_decision_service.py tests/test_upload_validation.py tests/test_user_model.py tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/auth.py src/vault/api/routes/organizations.py src/vault/api/routes/documents.py tests/test_auth_registration_api.py tests/test_organization_create_api.py tests/test_document_upload_api.py tests/test_document_facts_api.py tests/test_control_flags_api.py tests/test_duplicate_detection_api.py tests/test_review_decision_api.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
docker --version
git status --short
```

Validation results:

```text
python -m pytest tests/test_auth_registration_api.py -q
Passed. 14 passed.

python -m pytest tests/test_organization_create_api.py -q
Passed. 19 passed.

python -m pytest tests/test_document_upload_api.py -q
Passed. 25 passed.

python -m pytest tests/test_document_facts_api.py -q
Passed. 43 passed.

python -m pytest tests/test_control_flags_api.py -q
Passed. 45 passed.

python -m pytest tests/test_duplicate_detection_api.py -q
Passed. 35 passed.

python -m pytest tests/test_review_decision_api.py -q
Passed. 47 passed.

Focused pytest groups
Passed. The full available test suite was covered in smaller groups. Grouped
runs passed with counts including 58, 88, 82, 139, 72, 98, 125, 94, 57, and
130 passed.

python -m py_compile ...
Passed.

Python line-length check for Step 34 edited Python files
Passed. No lines over 88 characters were found after wrapping two long lines.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

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

Definition of done:

* Registration creates a safe `user_registered` audit entry.
* Organization creation creates a safe `organization_created` audit entry.
* Document upload creates a safe `document_uploaded` audit entry.
* Document fact creation creates a safe `document_fact_created` audit entry.
* Control flag generation creates a safe `control_flags_generated` audit entry.
* Duplicate flag generation creates a safe `duplicate_flags_generated` audit
  entry.
* Review decision creation creates a safe `review_decision_created` audit entry.
* Review decision creation creates a safe `document_status_changed` audit entry
  when the document status actually changes.
* No status-change audit entry is created when the review keeps the same
  status.
* Audit entries are written in the same session as the successful state change.
* Failed validation requests do not create audit entries in this step.
* Unauthorized requests do not create audit entries.
* Viewer-denied state changes do not create audit entries.
* Audit entries use official action values.
* Audit entries use official entity type values.
* Audit entries are scoped to the correct organization where applicable.
* Audit metadata remains structured and safe.
* Audit metadata does not include raw passwords.
* Audit metadata does not include password hashes.
* Audit metadata does not include bearer tokens.
* Audit metadata does not include token payloads.
* Audit metadata does not include local absolute stored paths.
* No audit API route is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover audit wiring for each important state-changing route.
* Existing tests were validated in smaller groups due to sandbox timeout risk.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Wire audit entries into workflows
```


### Step 33 — Audit entry service

Status: Complete with documented environment limitations.

Goal:

* Add a directly testable audit entry service that can create, validate, list,
  and retrieve audit entries, without adding audit API routes or wiring audit
  entries into existing state-changing routes yet.

Completed work:

* Added `src/vault/audit/service.py`.
* Added typed `create_audit_entry()` service behavior.
* The service accepts a SQLAlchemy `Session`, optional organization ID,
  optional actor user ID, action, entity type, optional entity ID, summary, and
  optional metadata.
* The service creates an `AuditEntry` record with the supplied audit data.
* The service trims action, entity type, and summary values.
* Blank actions are rejected.
* Blank entity types are rejected.
* Blank summaries are rejected.
* Unsupported actions are rejected using the official Step 32 audit action
  values.
* Unsupported entity types are rejected using the official Step 32 audit entity
  type values.
* Omitted metadata stores an empty object.
* Explicit null metadata is rejected.
* Metadata lists, strings, numbers, booleans, and other non-object values are
  rejected.
* Caller-provided metadata is copied into a plain dictionary so later caller
  mutations do not unexpectedly alter the audit entry object.
* The created audit entry is added to the supplied session.
* The service flushes so generated IDs are available.
* The service does not commit automatically.
* Nullable organization IDs are allowed for future account-level or system
  events.
* Nullable actor user IDs are allowed for future system events.
* Nullable entity IDs are allowed.
* Added typed `list_audit_entries()` helper.
* Listing returns only audit entries for the requested organization.
* Listing excludes organization-null audit entries.
* Listing is deterministic, newest first by `created_at`, with `id` as a
  tie-breaker.
* Added typed `list_audit_entries_for_entity()` helper.
* Entity listing scopes by entity type and entity ID.
* Entity listing does not return entries for another entity type.
* Entity listing does not return entries for another entity ID.
* Added typed `get_audit_entry()` helper.
* Detail lookup scopes by both organization ID and audit entry ID.
* Added typed `require_audit_entry()` helper.
* Required lookup raises `AuditEntryNotFoundError` when a scoped entry is
  missing.
* Audit entries from another organization are not returned by scoped lookup.
* Organization-null audit entries are not returned by organization-scoped
  detail lookup.
* Added `AuditEntryValidationError` in `src/vault/exceptions.py`.
* Added `AuditEntryNotFoundError` in `src/vault/exceptions.py`.
* Added `tests/test_audit_entry_service.py`.
* Tests cover creation, validation, metadata handling, nullable fields,
  organization listing, entity listing, scoped detail lookup, safe not-found
  behavior, no automatic commit, and safe metadata examples.
* Existing Step 1 through Step 32 behavior remains compatible in the focused
  tested groups.
* No audit API routes, state-changing service audit wiring, CSV exports, sample
  output, CI files, local databases, migrations, or application container were
  added.

Files created or edited:

```text
src/vault/audit/service.py
src/vault/exceptions.py
tests/test_audit_entry_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_audit_entry_service.py -q
python -m pytest tests/test_audit_entry_model.py tests/test_audit_entry_service.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py tests/test_audit_entry_model.py tests/test_audit_entry_service.py tests/test_auth_login_api.py tests/test_auth_login_service.py tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py tests/test_control_flag_model.py tests/test_control_flag_service.py tests/test_control_flags_api.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_database_config.py tests/test_document_fact_model.py tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py tests/test_document_storage.py tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py tests/test_duplicate_detection_service.py tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py tests/test_organization_models.py tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py tests/test_package_import.py tests/test_passwords.py -q
python -m pytest tests/test_review_decision_api.py -q
python -m pytest tests/test_review_decision_model.py tests/test_review_decision_service.py tests/test_upload_validation.py tests/test_user_model.py tests/test_user_service.py -q
python -m py_compile src/vault/audit/service.py tests/test_audit_entry_service.py src/vault/exceptions.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_audit_entry_service.py -q
Passed. 45 passed.

python -m pytest tests/test_audit_entry_model.py tests/test_audit_entry_service.py tests/test_alembic_config.py -q
Passed. 95 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

Focused pytest groups
Passed. All available test files were covered in smaller groups. The grouped
runs passed with counts including 136, 114, 55, 40, 43, 79, 72, 54, 20, 45,
and 83 passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Python line-length check for Step 33 edited Python files
Passed. No lines over 88 characters were found.

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

Definition of done:

* Audit entry service exists.
* Service creates an `AuditEntry` record.
* Service validates required audit fields.
* Service rejects blank action, entity type, and summary.
* Service rejects unsupported action values.
* Service rejects unsupported entity type values.
* Service trims simple audit metadata strings.
* Service stores empty metadata when metadata is omitted.
* Service requires metadata to be object-like.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* Service allows nullable organization ID.
* Service allows nullable actor user ID.
* Service allows nullable entity ID.
* Audit listing helper exists.
* Audit entity listing helper exists.
* Audit detail helper exists.
* Required audit helper exists.
* Audit listing is scoped by organization ID.
* Audit detail lookup is scoped by organization ID and audit entry ID.
* Audit entries from another organization are not leaked.
* Organization-null audit entries are not returned through organization-scoped
  lookup.
* No audit API route is added yet.
* Existing state-changing services do not write audit entries yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover creation, validation, metadata handling, nullable fields,
  listing, entity lookup, scoped detail lookup, and safe metadata examples.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Focused pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add audit entry service
```


### Step 29 — Review decision model and migration

Status: Complete with documented environment limitations.

Goal:

* Add the initial `ReviewDecision` SQLAlchemy model and one Alembic migration
  that creates the `review_decisions` table, without adding review service or
  API behavior yet.

Completed work:

* Added `src/vault/reviews/__init__.py`.
* Added `src/vault/reviews/decisions.py`.
* Defined official review decision values as `approved`, `rejected`, and
  `needs_info`.
* Confirmed `pending` is not an official review decision value.
* Added `src/vault/reviews/models.py`.
* Added a typed SQLAlchemy 2-style `ReviewDecision` ORM model.
* Added the official review decision fields: `id`, `document_id`,
  `reviewer_user_id`, `decision`, `reason`, and `created_at`.
* Used UUID primary keys for review decisions.
* Used the existing UTC-aware timestamp helper for `created_at`.
* Added non-null constraints for all official review decision fields.
* Added reasonable string lengths for decision and reason.
* Added a foreign key from `review_decisions.document_id` to `documents.id`.
* Added a foreign key from `review_decisions.reviewer_user_id` to `users.id`.
* Added a review decision check constraint for the official decision values.
* Added lookup indexes for document ID, reviewer user ID, and decision.
* Added a non-unique composite index on document ID and created-at timestamp
  for future review history queries.
* Did not add a uniqueness constraint, so multiple review decisions for the
  same document remain allowed.
* Updated `src/vault/models.py` so shared model metadata imports
  `ReviewDecision`.
* Added `alembic/versions/0007_create_review_decisions.py`.
* The migration creates only the `review_decisions` table and supporting
  indexes.
* The migration downgrade drops only the supporting indexes and
  `review_decisions` table.
* Added `tests/test_review_decision_model.py`.
* Updated `tests/test_alembic_config.py` for the new migration file and
  Alembic target metadata.
* Existing Step 1 through Step 28 behavior remains compatible in the tested
  groups.
* No review service, review API route, document status transitions, audit
  logging, exports, sample output, CI files, local databases, or application
  container were added.

Files created or edited:

```text
src/vault/reviews/__init__.py
src/vault/reviews/decisions.py
src/vault/reviews/models.py
src/vault/models.py
alembic/versions/0007_create_review_decisions.py
tests/test_review_decision_model.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_review_decision_model.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py   tests/test_auth_login_api.py tests/test_auth_login_service.py   tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py   tests/test_control_flag_model.py tests/test_control_flag_service.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_current_user_dependency.py   tests/test_database_config.py tests/test_document_fact_model.py   tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py tests/test_document_storage.py   tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py -q
python -m pytest tests/test_duplicate_detection_service.py   tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py   tests/test_organization_models.py tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py tests/test_package_import.py   tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py   tests/test_user_service.py -q
python -m py_compile src/vault/reviews/__init__.py   src/vault/reviews/decisions.py src/vault/reviews/models.py   src/vault/models.py alembic/versions/0007_create_review_decisions.py   tests/test_review_decision_model.py tests/test_alembic_config.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_review_decision_model.py   tests/test_alembic_config.py -q
Passed. 42 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

Focused pytest groups
Passed. The groups listed in Current validation status all passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0007_create_review_decisions as head.

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

Definition of done:

* `ReviewDecision` ORM model exists.
* `review_decisions` table metadata matches Project State fields.
* `document_id` links review decisions to documents.
* `reviewer_user_id` links review decisions to users.
* Required review fields are non-null.
* Official review decision values are defined.
* `pending` is not an official review decision.
* Review decision constraint exists.
* Useful lookup indexes exist.
* Multiple review decisions for the same document are still allowed.
* Shared model metadata includes `review_decisions`.
* Alembic target metadata includes `review_decisions`.
* Migration `0007_create_review_decisions.py` exists.
* Migration creates only `review_decisions` and supporting indexes.
* Migration downgrade drops only `review_decisions` and supporting indexes.
* No review service is added yet.
* No review API route is added yet.
* No document status transitions are added yet.
* No audit logging is added yet.
* No exports are added yet.
* Tests cover model structure, official values, constraints, indexes,
  metadata, and migration presence.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add review decision model
```



### Step 30 — Review decision service

Status: Complete with documented environment limitations.

Goal:

* Add a directly testable review decision service that records required review
  decisions and updates the linked document status, without adding API routes
  or audit logging yet.

Completed work:

* Added `src/vault/reviews/service.py`.
* Added typed `create_review_decision()` service behavior.
* The service accepts a SQLAlchemy `Session`, document ID, reviewer user ID,
  decision, and reason.
* The service loads the target `Document` by document ID.
* Missing target documents raise `ReviewDecisionNotFoundError`.
* The service creates a `ReviewDecision` record with document ID, reviewer user
  ID, decision, reason, and generated metadata.
* The service trims decision and reason values.
* Blank decisions are rejected.
* Blank reasons are rejected.
* Whitespace-only reasons are rejected.
* Unsupported decisions are rejected.
* `pending` is rejected as a review decision.
* A reason is required for approved, rejected, and needs-info decisions.
* The decision-to-status mapping is explicit and readable.
* `approved` review decisions update the linked document status to `approved`.
* `rejected` review decisions update the linked document status to `rejected`.
* `needs_info` review decisions update the linked document status to
  `needs_info`.
* Review decision records are added to the supplied session.
* The service flushes so generated review decision IDs are available.
* The service does not commit automatically.
* Multiple review decisions for the same document are still allowed.
* Later review decisions may update the document status again.
* The service does not verify organization membership yet.
* The service does not write audit entries yet.
* Added typed `list_review_decisions()` helper.
* Listing returns only decisions for the requested document.
* Listing uses deterministic oldest-first ordering by `created_at`, with `id`
  as a tie-breaker.
* Added typed `get_review_decision()` helper.
* Detail lookup scopes by both document ID and review decision ID.
* Added typed `require_review_decision()` helper.
* Required lookup raises `ReviewDecisionNotFoundError` when a scoped decision is
  missing.
* Review decisions from another document are not returned by scoped lookup.
* Added `ReviewDecisionValidationError` in `src/vault/exceptions.py`.
* Added `ReviewDecisionNotFoundError` in `src/vault/exceptions.py`.
* Added `tests/test_review_decision_service.py`.
* Existing Step 1 through Step 29 behavior remains compatible in the tested
  groups.
* No review API routes, organization route-level review permissions, audit
  logging, CSV exports, sample output, CI files, local databases, migrations,
  or application container were added.

Files created or edited:

```text
src/vault/reviews/service.py
src/vault/exceptions.py
tests/test_review_decision_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_review_decision_service.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py   tests/test_auth_login_api.py tests/test_auth_login_service.py   tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py   tests/test_control_flag_model.py tests/test_control_flag_service.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_current_user_dependency.py   tests/test_database_config.py tests/test_document_fact_model.py   tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py tests/test_document_storage.py   tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py -q
python -m pytest tests/test_duplicate_detection_service.py   tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py   tests/test_organization_models.py tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py   tests/test_package_import.py tests/test_passwords.py   tests/test_review_decision_model.py tests/test_review_decision_service.py   tests/test_upload_validation.py tests/test_user_model.py   tests/test_user_service.py -q
python -m py_compile src/vault/reviews/__init__.py   src/vault/reviews/decisions.py src/vault/reviews/models.py   src/vault/reviews/service.py src/vault/exceptions.py   tests/test_review_decision_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_review_decision_service.py -q
Passed. 29 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

Focused pytest groups
Passed. The groups listed in Current validation status all passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0007_create_review_decisions as head.

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

Definition of done:

* Review decision service exists.
* Service creates a `ReviewDecision` record.
* Service validates required review fields.
* Service rejects blank decisions.
* Service rejects blank reasons.
* Service rejects unsupported decisions.
* Service rejects `pending` as a review decision.
* Service requires a reason for every decision.
* Service trims simple review metadata strings.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* Service updates document status for approved, rejected, and needs-info
  decisions.
* Multiple review decisions for the same document are still allowed.
* Later review decisions can update document status again.
* Review decision listing helper exists.
* Review decision detail helper exists.
* Required review decision helper exists.
* Review decision lookup is scoped by document ID and review decision ID.
* Review decisions from another document are not leaked.
* No review API route is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover creation, validation, status transitions, duplicate history
  allowance, listing, scoped lookup, and safe not-found behavior.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add review decision service
```


### Step 31 — Review decision API route

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped review decision API routes that allow
  owners and reviewers to submit review decisions for existing documents, and
  allow owners, reviewers, and viewers to list and read safe review metadata.

Completed work:

* Added `src/vault/reviews/schemas.py`.
* Added `ReviewDecisionCreateRequest` with `decision` and `reason`.
* Added `ReviewDecisionResponse` with safe review metadata fields only.
* Updated the existing documents router with review decision routes.
* Added `POST /organizations/{organization_id}/documents/{document_id}/review`.
* Added `GET /organizations/{organization_id}/documents/{document_id}/reviews`.
* Added `GET /organizations/{organization_id}/documents/{document_id}/reviews/{review_decision_id}`.
* Review routes require authentication through the existing current-user
  dependency chain.
* Review routes require organization membership through the existing
  `require_organization_roles()` dependency factory.
* Review creation explicitly allows owners and reviewers.
* Review creation rejects viewers, non-members, and unknown organizations.
* Review listing and detail explicitly allow owners, reviewers, and viewers.
* Review listing and detail reject non-members and unknown organizations with
  the existing safe HTTP 403 behavior.
* Review routes verify the path document belongs to the path organization before
  creating, listing, or reading review decisions.
* Documents from another organization are rejected through review routes.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Review creation calls the Step 30 `create_review_decision()` service.
* Review listing calls the Step 30 `list_review_decisions()` service.
* Review detail calls the Step 30 `require_review_decision()` service.
* Successful review creation commits and refreshes the created review decision
  and linked document.
* Review validation errors return HTTP 400 with safe public messages.
* Missing review detail returns HTTP 404 with a safe public message.
* Review responses include only `id`, `document_id`, `reviewer_user_id`,
  `decision`, `reason`, and `created_at`.
* Review responses do not expose local absolute stored paths, raw passwords,
  password hashes, or token internals.
* Multiple review decisions for the same document remain allowed through the
  API.
* Later review decisions can update document status again through the API.
* Added `tests/test_review_decision_api.py`.
* Tests cover successful review creation, role behavior, authentication
  failures, validation failures, status transitions, organization scoping,
  document scoping, review scoping, safe responses, OpenAPI inclusion, and the
  absence of audit entries in this step.
* Existing Step 1 through Step 30 behavior remains compatible in the tested
  groups.
* No audit logging, CSV exports, sample output, CI files, local databases,
  migrations, or application container were added.

Files created or edited:

```text
src/vault/api/routes/documents.py
src/vault/reviews/schemas.py
src/vault/exceptions.py
tests/test_review_decision_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_review_decision_api.py -q
python -m pytest tests/test_review_decision_service.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py   tests/test_auth_login_api.py tests/test_auth_login_service.py   tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py   tests/test_control_flag_model.py tests/test_control_flag_service.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_current_user_dependency.py   tests/test_database_config.py tests/test_document_fact_model.py   tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py   tests/test_document_storage.py tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py -q
python -m pytest tests/test_duplicate_detection_service.py   tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py   tests/test_organization_models.py tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py   tests/test_package_import.py tests/test_passwords.py   tests/test_review_decision_model.py tests/test_review_decision_service.py   tests/test_upload_validation.py tests/test_user_model.py tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py   src/vault/reviews/schemas.py src/vault/reviews/service.py   src/vault/exceptions.py tests/test_review_decision_api.py   tests/test_review_decision_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_review_decision_api.py -q
Passed. 45 passed.

python -m pytest tests/test_review_decision_service.py -q
Passed. 29 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

Focused pytest groups
Passed. The groups listed in Current validation status all passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0007_create_review_decisions as head.

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

Definition of done:

* Review decision request schema exists.
* Review decision response schema exists.
* Review create, list, and detail routes exist.
* Review routes require authentication.
* Review routes require organization membership.
* Owners and reviewers can submit review decisions.
* Viewers can list and read review decisions.
* Viewers cannot submit review decisions.
* Non-members cannot submit, list, or read review decisions.
* Missing, invalid, expired, unknown-user, and inactive-user tokens return
  authentication errors.
* Review creation verifies the document belongs to the organization.
* Documents from other organizations cannot be used through review routes.
* Missing documents return safe not-found behavior.
* Review creation validates review input.
* Review creation persists a `ReviewDecision` row.
* Review creation updates document status.
* Review listing is scoped to the requested document.
* Review detail lookup is scoped by document ID and review decision ID.
* Review decisions from other documents are not leaked.
* Responses return safe review metadata.
* Routes appear in OpenAPI.
* Multiple review decisions for the same document are still allowed.
* Later review decisions can update document status again.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover successful review creation, role behavior, auth failure,
  validation failure, status transitions, organization scoping, document
  scoping, review scoping, safe responses, and OpenAPI inclusion.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add review decision API route
```


### Step 32 — Audit entry model and migration

Status: Complete with documented environment limitations.

Goal:

* Add the initial `AuditEntry` SQLAlchemy model and one Alembic migration that
  creates the `audit_entries` table, without adding audit service or API
  behavior yet.

Completed work:

* Added `src/vault/audit/__init__.py`.
* Added `src/vault/audit/actions.py`.
* Defined official audit action values as `user_registered`,
  `organization_created`, `document_uploaded`, `document_fact_created`,
  `control_flags_generated`, `duplicate_flags_generated`,
  `review_decision_created`, `document_status_changed`, and
  `export_generated`.
* Added `src/vault/audit/entities.py`.
* Defined official audit entity type values as `user`, `organization`,
  `document`, `document_fact`, `control_flag`, `review_decision`, and
  `export`.
* Added `src/vault/audit/models.py`.
* Added a typed SQLAlchemy 2-style `AuditEntry` ORM model.
* Added the official audit entry fields: `id`, `organization_id`,
  `actor_user_id`, `action`, `entity_type`, `entity_id`, `summary`,
  `metadata_json`, and `created_at`.
* Used UUID primary keys for audit entries.
* Used the existing UTC-aware timestamp helper for `created_at`.
* Made `organization_id`, `actor_user_id`, and `entity_id` nullable for future
  account-level, system-generated, export, or mixed-entity events.
* Added a foreign key from `audit_entries.organization_id` to
  `organizations.id`.
* Added a foreign key from `audit_entries.actor_user_id` to `users.id`.
* Intentionally did not add a foreign key for `entity_id` because entity ID can
  point to different tables depending on entity type.
* Required `action`, `entity_type`, `summary`, `metadata_json`, and
  `created_at`.
* Used SQLAlchemy `JSON` for `metadata_json`.
* Added a safe empty-object model default for `metadata_json`.
* Added reasonable string lengths for action, entity type, and summary.
* Added audit action and entity type check constraints.
* Added lookup indexes for organization ID, actor user ID, action, entity type,
  and created-at timestamp.
* Added composite indexes for organization ID plus created-at and entity type
  plus entity ID.
* Did not add uniqueness constraints.
* Updated `src/vault/models.py` so shared model metadata imports `AuditEntry`.
* Added `alembic/versions/0008_create_audit_entries.py`.
* The migration creates only the `audit_entries` table and supporting indexes.
* The migration downgrade drops only the supporting indexes and
  `audit_entries` table.
* Added `tests/test_audit_entry_model.py`.
* Updated `tests/test_alembic_config.py` for the new migration file and
  Alembic target metadata.
* Existing Step 1 through Step 31 behavior remains compatible in the focused
  tested groups.
* No audit service, audit API route, state-changing service audit wiring, CSV
  exports, sample output, CI files, local databases, or application container
  were added.

Files created or edited:

```text
src/vault/audit/__init__.py
src/vault/audit/actions.py
src/vault/audit/entities.py
src/vault/audit/models.py
src/vault/models.py
alembic/versions/0008_create_audit_entries.py
tests/test_audit_entry_model.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_audit_entry_model.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py   tests/test_auth_login_api.py tests/test_auth_login_service.py   tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py   tests/test_control_flag_model.py tests/test_control_flag_service.py -q
python -m py_compile src/vault/audit/__init__.py   src/vault/audit/actions.py src/vault/audit/entities.py   src/vault/audit/models.py src/vault/models.py   alembic/versions/0008_create_audit_entries.py   tests/test_audit_entry_model.py tests/test_alembic_config.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_audit_entry_model.py tests/test_alembic_config.py -q
Passed. 50 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. Focused audit and Alembic coverage passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py   tests/test_auth_login_api.py tests/test_auth_login_service.py   tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
Passed. 71 passed.

python -m pytest tests/test_auth_tokens.py tests/test_config.py   tests/test_control_flag_model.py tests/test_control_flag_service.py -q
Passed. 65 passed.

python -m py_compile ...
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0008_create_audit_entries as head.

Python line-length check for Step 32 edited Python files
Passed. No lines over 88 characters were found.

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

Definition of done:

* `AuditEntry` ORM model exists.
* `audit_entries` table metadata matches Project State fields.
* `organization_id` can link audit entries to organizations and is nullable.
* `actor_user_id` can link audit entries to users and is nullable.
* `entity_id` is nullable and does not have a foreign key.
* Required audit fields are non-null.
* Official audit action values are defined.
* Official audit entity type values are defined.
* Audit action constraint exists.
* Audit entity type constraint exists.
* Useful lookup indexes exist.
* Composite future-query indexes exist.
* Shared model metadata includes `audit_entries`.
* Alembic target metadata includes `audit_entries`.
* Migration `0008_create_audit_entries.py` exists.
* Migration creates only `audit_entries` and supporting indexes.
* Migration downgrade drops only `audit_entries` and supporting indexes.
* No audit service is added yet.
* No audit API route is added yet.
* Existing state-changing services do not write audit entries yet.
* No exports are added yet.
* Tests cover model structure, official values, constraints, indexes, metadata,
  and migration presence.
* Focused pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add audit entry model
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


### Step 17 — Secure upload validation helpers

Status: Complete with documented environment limitations.

Goal:

* Add directly testable secure upload validation helpers that validate file
  metadata before storage and document creation, without writing files or
  adding API routes yet.

Completed work:

* Added `src/vault/documents/validation.py`.
* Added typed `ValidatedUploadMetadata` result data.
* Added typed `validate_upload_metadata()` helper.
* The helper accepts `original_filename`, `content_type`, and
  `file_size_bytes` only.
* Defined explicit MVP allowed extensions: `.csv`, `.txt`, and `.pdf`.
* Defined explicit MVP allowed content types: `text/csv`, `text/plain`, and
  `application/pdf`.
* Defined explicit `MAX_UPLOAD_SIZE_BYTES` as 5 MiB.
* Validation trims surrounding whitespace from display filename metadata only.
* Validation preserves a safe display filename in the returned result.
* Validation normalizes the returned extension to lowercase.
* Extension matching is case-insensitive.
* Blank filenames are rejected.
* Whitespace-only filenames are rejected.
* Filenames containing forward slashes are rejected.
* Filenames containing backslashes are rejected.
* Obvious path traversal attempts are rejected.
* Hidden filenames are rejected.
* Extensionless filenames are rejected.
* Unsupported extensions are rejected.
* Unsupported content types are rejected.
* Mismatched extension/content-type pairs are rejected.
* Zero-byte files are rejected.
* Negative file sizes are rejected.
* Files larger than the configured maximum are rejected.
* Files exactly at the configured maximum are accepted.
* Added `DocumentUploadValidationError` in `src/vault/exceptions.py`.
* Kept the helper framework-independent and directly testable.
* Confirmed validation performs no file I/O.
* Existing document metadata service behavior remains unchanged.
* No database migrations were added because the `documents` table did not
  change.
* No upload routes, multipart handling, file storage writes, stored filename
  generation, SHA-256 hashing from bytes, document metadata routes, document
  listing/detail routes, document facts, control flags, duplicate detection,
  review decisions, audit logging, CSV exports, sample input/output generation,
  CI files, local databases, or application container were added.

Files created or edited:

```text
src/vault/documents/validation.py
src/vault/exceptions.py
tests/test_upload_validation.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_upload_validation.py -q
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
python -m pytest tests/test_upload_validation.py -q
24 passed.

python -m pytest -q
249 passed.

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
Step 17 is complete in the uploaded runtime with documented tooling
limitations. Pytest, CLI help, and Alembic history passed. Ruff, mypy, Bandit,
pip-audit, git status, and Docker-backed migration checks should be run locally
before committing.
```

Definition of done:

* Upload metadata validation helper exists.
* Allowed extensions are explicit.
* Allowed content types are explicit.
* Maximum upload size is explicit.
* Valid `.csv`, `.txt`, and `.pdf` metadata is accepted.
* Blank filenames are rejected.
* Path separators and path traversal are rejected.
* Unsupported extensions are rejected.
* Unsupported content types are rejected.
* Invalid file sizes are rejected.
* Oversized files are rejected.
* Validation returns normalized safe display metadata.
* Validation performs no file I/O.
* No upload route is added yet.
* No file storage writes are added yet.
* No SHA-256 hashing from bytes is added yet.
* No document facts are added yet.
* No audit logging is added yet.
* No migrations are added in this step.
* Tests cover upload validation behavior.
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
Add secure upload validation helpers
```


### Step 18 — File storage and hashing helpers

Status: Complete with documented environment limitations.

Goal:

* Add directly testable local file storage and SHA-256 hashing helpers that can
  safely persist already-validated upload bytes outside the source tree,
  without adding API routes or database writes yet.

Completed work:

* Added `src/vault/documents/storage.py`.
* Added typed `StoredUpload` result data.
* Added typed `calculate_sha256()` helper.
* SHA-256 output is lowercase hexadecimal.
* Added typed `generate_stored_filename()` helper.
* Stored filenames are generated by Vault and do not include user-provided
  original filename text.
* Stored filenames use a random UUID-style value.
* Stored filenames preserve validated `.csv`, `.txt`, and `.pdf` extensions.
* Stored filename generation rejects unsupported extensions.
* Stored filename generation rejects malformed extensions.
* Stored filenames do not include path separators.
* Added typed `store_upload_bytes()` helper.
* The storage helper creates the supplied upload directory if it is missing.
* The storage helper rejects empty bytes.
* The storage helper rejects bytes larger than the upload validation maximum.
* The storage helper writes bytes to a generated filename under the supplied
  upload directory.
* The storage helper uses exclusive file creation so target filename collisions
  fail safely instead of overwriting existing files.
* The storage helper returns stored filename, full stored path, file size, and
  SHA-256 hash.
* The storage helper does not accept or use the user-provided original
  filename.
* The storage helper performs no FastAPI request handling and requires no
  FastAPI imports.
* The storage helper performs no database access and creates no `Document`
  records.
* No database migrations were added because the `documents` table did not
  change.
* No upload routes, multipart handling, document listing/detail routes,
  document facts, control flags, duplicate detection, review decisions, audit
  logging, CSV exports, sample input/output generation, CI files, local
  databases, or application container were added.

Files created or edited:

```text
src/vault/documents/storage.py
tests/test_document_storage.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_storage.py -q
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
python -m pytest tests/test_document_storage.py -q
25 passed.

python -m pytest -q
274 passed.

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
Step 18 is complete in the uploaded runtime with documented tooling
limitations. Pytest, CLI help, and Alembic history passed. Ruff, mypy, Bandit,
pip-audit, git status, and Docker-backed migration checks should be run locally
before committing.
```

Definition of done:

* SHA-256 helper exists.
* Safe stored filename generation helper exists.
* Local upload byte storage helper exists.
* Stored filenames are generated by Vault.
* Stored filenames preserve validated extensions.
* Stored filenames do not include user-provided filename text.
* Stored filenames do not include path separators.
* Storage writes only inside the supplied upload directory.
* Storage creates the upload directory if missing.
* Storage returns stored filename, stored path, file size, and SHA-256 hash.
* Empty uploads are rejected.
* Oversized uploads are rejected.
* Filename collisions fail safely.
* No upload route is added yet.
* No database document creation is added in this step.
* No document facts are added yet.
* No audit logging is added yet.
* No migrations are added in this step.
* Tests cover storage and hashing behavior.
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
Add file storage and hashing helpers
```

### Step 19 — Document upload API route

Status: Complete with documented environment limitations.

Goal:

* Add an authenticated, organization-scoped document upload API route that
  accepts a file upload, validates metadata, stores bytes safely, creates a
  `Document` metadata record, commits the database transaction, and returns
  safe document metadata.

Completed work:

* Added `python-multipart` as a runtime dependency for FastAPI multipart file
  uploads.
* Added `src/vault/documents/schemas.py`.
* Added `DocumentUploadResponse` as an explicit safe document response schema.
* The response schema includes `id`, `organization_id`,
  `uploaded_by_user_id`, `original_filename`, `stored_filename`,
  `content_type`, `file_size_bytes`, `sha256_hash`, `status`, and
  `created_at`.
* The response schema does not include local absolute stored paths, token
  internals, raw passwords, or password hashes.
* Added `src/vault/api/routes/documents.py`.
* Added `POST /organizations/{organization_id}/documents/upload`.
* Included the documents router in the FastAPI app factory.
* Updated the app description to include document upload as implemented
  behavior and keep reviews, audit logs, and exports as planned later.
* The upload route requires authentication through the existing current-user
  dependency.
* The upload route requires organization membership through the existing
  `require_organization_roles()` dependency factory.
* The upload route explicitly allows owners and reviewers.
* The upload route rejects viewers, non-members, and unknown organizations with
  HTTP 403.
* Missing, invalid, expired, unknown-user, and inactive-user tokens continue to
  return HTTP 401.
* The upload route accepts one uploaded file field named `file`.
* The upload route validates filename, content type, and file size with the
  existing Step 17 upload validation helper.
* The upload route reads file bytes after reasonable metadata validation when
  the multipart parser provides file size metadata.
* The upload route safely falls back to reading bytes first only when the
  uploaded file size is unavailable from the framework object.
* The upload route stores bytes with the existing Step 18 storage helper.
* Stored filenames are generated by Vault and do not use original filenames as
  paths.
* The upload route creates document metadata with the existing Step 16 document
  metadata service.
* The upload route uses the authenticated user as `uploaded_by_user_id`.
* The upload route uses the path `organization_id` as the document
  organization.
* The upload route commits successful uploads after storage and metadata
  creation both succeed.
* The upload route refreshes the created document before returning.
* Upload validation and document metadata validation errors return HTTP 400.
* If storage succeeds but database commit later fails, Step 19 does not yet
  delete the stored file as rollback cleanup; this behavior is documented and
  cleanup is deferred.
* Added `tests/test_document_upload_api.py`.
* Tests cover owner upload, reviewer upload, viewer denial, non-member denial,
  unknown-organization denial, missing token, invalid token, expired token, and
  inactive-user token behavior.
* Tests cover successful HTTP 201 upload responses and safe response metadata.
* Tests confirm responses do not include local absolute stored paths, raw
  passwords, or password hashes.
* Tests confirm successful upload creates a `Document` row.
* Tests confirm the document row stores organization ID, uploader user ID,
  original filename, generated stored filename, content type, file size,
  SHA-256 hash, and pending status.
* Tests confirm uploaded bytes are written under the configured temporary upload
  directory.
* Tests confirm uploaded bytes are not written using the original filename as a
  path.
* Tests cover invalid extension, invalid content type, mismatched extension and
  content type, empty upload, and oversized upload.
* Tests confirm the upload route appears in OpenAPI.
* Tests use temporary upload directories and dependency-overridden database
  sessions, so they do not require Docker, PostgreSQL, network ports, real
  credentials, or private environment variables.
* No database migration was added because the `documents` table did not change.
* No document listing route, detail route, download route, document facts,
  duplicate detection, review decisions, audit logging, CSV exports, sample
  input/output generation, CI files, local databases, or application container
  were added.

Files created or edited:

```text
pyproject.toml
src/vault/api/main.py
src/vault/api/routes/documents.py
src/vault/documents/schemas.py
tests/test_document_upload_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_upload_api.py -q
python -m pytest -q
python -m pytest tests/test_package_import.py tests/test_passwords.py \
  tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/api/main.py \
  tests/test_document_upload_api.py
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
python -m pytest tests/test_document_upload_api.py -q
Passed. 22 passed.

python -m pytest -q
Attempted. The sandbox command timed out after reaching late test progress,
not after a reported test failure.

python -m pytest tests/test_package_import.py tests/test_passwords.py \
  tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 48 passed.

python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/api/main.py \
  tests/test_document_upload_api.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users,
0003_orgs_memberships, and 0004_create_documents as head. No Step 19
migration was added.

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
Step 19 is complete in the uploaded runtime with documented tooling
limitations. The new upload API test file passed, CLI help passed, Alembic
history passed, and syntax compilation passed. Full pytest was attempted but
timed out in the sandbox after late progress without a reported failure; the
remaining tail test files were run separately and passed. Ruff, mypy, Bandit,
pip-audit, git status, and Docker-backed migration checks should be run locally
before committing.
```

Definition of done:

* `POST /organizations/{organization_id}/documents/upload` exists.
* Upload route requires authentication.
* Upload route requires organization membership.
* Upload route allows owners.
* Upload route allows reviewers.
* Upload route rejects viewers.
* Upload route rejects non-members.
* Upload route validates upload metadata.
* Upload route stores bytes using Vault-generated stored filenames.
* Upload route creates a `Document` metadata record.
* Upload route commits successful uploads.
* Upload route returns safe document metadata.
* Upload route does not expose absolute local paths.
* Upload route does not expose raw passwords.
* Upload route does not expose password hashes.
* Upload route appears in OpenAPI.
* No document facts are added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover successful upload, role behavior, auth failure, validation
  failure, storage behavior, and database metadata creation.
* Existing tests were partially validated in this environment; local full-suite
  validation is still recommended before committing.
* Pytest for the new upload API file passes.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document upload API route
```



### Step 20 — Document listing and detail routes

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped document listing and document detail
  API routes that return safe document metadata only, without adding downloads
  or document facts yet.

Completed work:

* Added `DocumentResponse` as a generic safe document metadata response schema.
* Kept `DocumentUploadResponse` available for the existing upload route by
  deriving it from the generic document response schema.
* Added `DocumentNotFoundError` as a safe custom document service exception.
* Added `list_documents_for_organization()` in
  `src/vault/documents/service.py`.
* Added `get_document_for_organization()` in
  `src/vault/documents/service.py`.
* Added `require_document_for_organization()` in
  `src/vault/documents/service.py`.
* Document listing is scoped by organization ID.
* Document listing returns newest documents first by `created_at`, with `id` as
  a deterministic tie-breaker.
* Document detail lookup scopes by both organization ID and document ID.
* Missing document detail raises a safe custom exception at the service layer.
* Added `GET /organizations/{organization_id}/documents`.
* Added `GET /organizations/{organization_id}/documents/{document_id}`.
* Reused the existing documents router from Step 19.
* Both read routes require authentication through the existing current-user
  dependency chain.
* Both read routes require organization membership through the existing
  `require_organization_roles()` dependency factory.
* Both read routes explicitly allow owners, reviewers, and viewers.
* Non-members and unknown organizations are rejected with the existing safe
  HTTP 403 organization-access behavior.
* Missing, invalid, expired, unknown-user, and inactive-user tokens continue to
  return HTTP 401 before document read behavior runs.
* Missing documents return HTTP 404 with a safe public not-found message.
* Detail lookup does not return documents from another organization even when
  the path organization is accessible.
* Read responses include only safe document metadata: `id`, `organization_id`,
  `uploaded_by_user_id`, `original_filename`, `stored_filename`,
  `content_type`, `file_size_bytes`, `sha256_hash`, `status`, and
  `created_at`.
* Read responses do not expose local absolute stored paths, token internals,
  raw passwords, or password hashes.
* Added `tests/test_document_read_api.py`.
* Added service read-helper coverage in `tests/test_document_service.py`.
* Route tests cover owner, reviewer, and viewer list/detail access.
* Route tests cover non-member denial.
* Route tests cover missing, invalid, expired, and inactive-user token behavior.
* Route tests cover organization scoping and cross-organization leak
  prevention.
* Route tests cover safe response metadata and OpenAPI inclusion.
* Service tests cover organization-scoped listing, deterministic ordering,
  scoped detail lookup, and safe not-found exceptions.
* Existing Step 1 through Step 19 behavior remains compatible in the tested
  groups.
* No file download route, serving local uploaded files, document facts, control
  flags, duplicate detection, reviews, audit logs, CSV exports, sample outputs,
  migrations, CI files, local databases, or application container were added.

Files created or edited:

```text
src/vault/api/main.py
src/vault/api/routes/documents.py
src/vault/documents/schemas.py
src/vault/documents/service.py
src/vault/exceptions.py
tests/test_document_read_api.py
tests/test_document_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
python -m pytest -q
python -m pytest tests/test_document_storage.py \
  tests/test_document_upload_api.py tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py \
  tests/test_organization_models.py -q
python -m pytest tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_config.py \
  tests/test_current_user_dependency.py tests/test_database_config.py \
  tests/test_document_model.py tests/test_document_read_api.py \
  tests/test_document_service.py -q
python -m pytest tests/test_organization_service.py \
  tests/test_package_import.py tests/test_passwords.py \
  tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/documents/service.py \
  src/vault/exceptions.py tests/test_document_read_api.py \
  tests/test_document_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
Passed. 62 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_document_storage.py \
  tests/test_document_upload_api.py tests/test_organization_access_service.py -q
Passed. 63 passed.

python -m pytest tests/test_organization_create_api.py \
  tests/test_organization_models.py -q
Passed. 34 passed.

python -m pytest tests/test_organization_rbac_dependency.py -q
Passed. 20 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_config.py \
  tests/test_current_user_dependency.py tests/test_database_config.py \
  tests/test_document_model.py tests/test_document_read_api.py \
  tests/test_document_service.py -q
Passed. 154 passed.

python -m pytest tests/test_organization_service.py \
  tests/test_package_import.py tests/test_passwords.py \
  tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 59 passed.

python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/documents/service.py \
  src/vault/exceptions.py tests/test_document_read_api.py \
  tests/test_document_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0001_baseline, 0002_create_users,
0003_orgs_memberships, and 0004_create_documents as head. No Step 20
migration was added.

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
Step 20 is complete in the uploaded runtime with documented tooling
limitations. The new read API and service tests passed, CLI help passed,
Alembic history passed, and syntax compilation passed. Full pytest was
attempted but timed out in the sandbox without a reported failure, so the suite
was run in smaller groups and those groups passed. Ruff, mypy, Bandit,
pip-audit, git status, and Docker-backed migration checks should be run locally
before committing.
```

Definition of done:

* `GET /organizations/{organization_id}/documents` exists.
* `GET /organizations/{organization_id}/documents/{document_id}` exists.
* List route requires authentication.
* Detail route requires authentication.
* List route requires organization membership.
* Detail route requires organization membership.
* Owners can list/read documents.
* Reviewers can list/read documents.
* Viewers can list/read documents.
* Non-members cannot list/read documents.
* Missing/invalid/expired tokens return authentication errors.
* Listing is scoped to the requested organization.
* Detail lookup is scoped by both organization ID and document ID.
* Documents from other organizations are not leaked.
* Missing documents return safe not-found behavior.
* Responses return safe document metadata.
* Responses do not expose absolute local paths.
* Responses do not expose raw passwords.
* Responses do not expose password hashes.
* Routes appear in OpenAPI.
* No file download route is added yet.
* No document facts are added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover successful reads, role behavior, auth failure, organization
  scoping, safe responses, and not-found behavior.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document read API routes
```


### Step 21 — Document facts model and migration

Status: Complete with documented environment limitations.

Goal:

* Add the initial structured `DocumentFact` SQLAlchemy model and one Alembic
  migration that creates the `document_facts` table, without adding facts
  service or API behavior yet.

Completed work:

* Added `DocumentFact` to `src/vault/documents/models.py`.
* The model represents structured fake invoice or receipt facts linked to a
  document.
* Added the official document fact fields: `id`, `document_id`, `vendor_name`,
  `invoice_number`, `invoice_date`, `due_date`, `amount_cents`, `currency`,
  `category`, `memo`, and `created_at`.
* Used UUID primary keys for document facts.
* Used the existing UTC-aware timestamp helper for `created_at`.
* Added a non-null foreign key from `document_facts.document_id` to
  `documents.id`.
* Kept `vendor_name`, `amount_cents`, `currency`, and `category` required.
* Kept `invoice_number`, `invoice_date`, `due_date`, and `memo` optional.
* Added reasonable string lengths for vendor name, invoice number, currency,
  category, and memo.
* Added a model-level default currency of `USD`.
* Added a check constraint requiring `amount_cents` to be positive.
* Added a check constraint requiring currency to be uppercase three-letter text.
* Added lookup indexes for `document_id`, `vendor_name`, and `invoice_number`.
* Added a non-unique composite index on vendor name, invoice number, and amount
  cents for future duplicate detection.
* Did not add a uniqueness constraint, so duplicate invoice facts remain
  allowed.
* Updated `src/vault/models.py` so shared model metadata imports
  `DocumentFact`.
* Added `alembic/versions/0005_create_document_facts.py`.
* The migration creates only the `document_facts` table and its supporting
  indexes.
* The migration downgrade drops only the supporting indexes and
  `document_facts` table.
* Added `tests/test_document_fact_model.py`.
* Updated `tests/test_alembic_config.py` for the new migration file and
  Alembic target metadata.
* Existing Step 1 through Step 20 behavior remains compatible in the tested
  groups.
* No document facts service, document facts API route, parsing, control flags,
  duplicate detection behavior, review decisions, audit logging, exports,
  sample output, CI files, local databases, or application container were
  added.

Files created or edited:

```text
src/vault/documents/models.py
src/vault/models.py
alembic/versions/0005_create_document_facts.py
tests/test_document_fact_model.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_fact_model.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_document_fact_model.py tests/test_document_model.py \
  tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/documents/models.py src/vault/models.py \
  alembic/versions/0005_create_document_facts.py \
  tests/test_document_fact_model.py tests/test_alembic_config.py
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
python -m pytest tests/test_document_fact_model.py tests/test_alembic_config.py -q
Passed. 35 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_document_fact_model.py tests/test_document_model.py \
  tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
Passed. 136 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 35 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 125 passed.

python -m py_compile src/vault/documents/models.py src/vault/models.py \
  alembic/versions/0005_create_document_facts.py \
  tests/test_document_fact_model.py tests/test_alembic_config.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0005_create_document_facts as head.

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

Definition of done:

* `DocumentFact` ORM model exists.
* `document_facts` table metadata matches Project State fields.
* `document_id` links facts to documents.
* Required fact fields are non-null.
* Optional fact fields are nullable.
* Positive amount constraint exists.
* Currency metadata is constrained.
* Useful lookup indexes exist.
* Duplicate facts are still allowed.
* Shared model metadata includes `document_facts`.
* Alembic target metadata includes `document_facts`.
* Migration `0005_create_document_facts.py` exists.
* Migration creates only `document_facts` and supporting indexes.
* Migration downgrade drops only `document_facts` and supporting indexes.
* No facts service is added yet.
* No facts API route is added yet.
* No control flags are added yet.
* No duplicate detection is added yet.
* No audit logging is added yet.
* No exports are added yet.
* Tests cover model structure, constraints, indexes, metadata, and migration
  presence.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document facts model
```



### Step 22 — Document facts service

Status: Complete with documented environment limitations.

Goal:

* Add a directly testable document facts service that creates, validates, lists,
  and retrieves structured document facts for an existing document, without
  adding API routes yet.

Completed work:

* Added `DocumentFactValidationError` in `src/vault/exceptions.py`.
* Added `DocumentFactNotFoundError` in `src/vault/exceptions.py`.
* Added typed `create_document_fact()` service behavior in
  `src/vault/documents/service.py`.
* The service accepts a SQLAlchemy `Session`, document ID, vendor name, amount
  cents, currency, category, and optional invoice number, invoice date, due
  date, and memo.
* The service creates a `DocumentFact` record and adds it to the supplied
  session.
* The service flushes so generated fact IDs are available.
* The service does not commit automatically.
* Vendor name, invoice number, currency, category, and memo are trimmed.
* Whitespace-only optional invoice numbers and memos are stored as `None`.
* Currency is normalized to uppercase.
* Blank vendor names are rejected.
* Blank currencies are rejected.
* Malformed currencies are rejected.
* Blank categories are rejected.
* Zero and negative amounts are rejected.
* Optional invoice number, invoice date, due date, and memo may be omitted.
* Duplicate facts are allowed for now.
* The service does not update document status.
* The service does not create control flags.
* The service does not verify organization membership.
* Added typed `list_document_facts()` helper.
* Fact listing is scoped to one document ID.
* Fact listing uses deterministic oldest-first ordering by `created_at`, with
  `id` as a tie-breaker.
* Added typed `get_document_fact()` helper.
* Fact detail lookup scopes by both document ID and fact ID.
* Added typed `require_document_fact()` helper.
* Missing required fact lookup raises a safe custom not-found exception.
* Facts from another document are not returned by scoped lookup.
* Added `tests/test_document_fact_service.py`.
* Existing Step 1 through Step 21 behavior remains compatible in the tested
  groups.
* No document facts API route, file parsing, CSV fact import, control flags,
  duplicate detection behavior, review decisions, audit logging, exports,
  sample output, CI files, local databases, migrations, or application
  container were added.

Files created or edited:

```text
src/vault/documents/service.py
src/vault/exceptions.py
tests/test_document_fact_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_fact_service.py -q
python -m pytest -q
python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_upload_api.py -q
python -m pytest tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/documents/service.py src/vault/exceptions.py \
  tests/test_document_fact_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_document_fact_service.py -q
Passed. 38 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
Passed. 65 passed.

python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
Passed. 62 passed.

python -m pytest tests/test_document_upload_api.py -q
Passed. 22 passed.

python -m pytest tests/test_document_storage.py -q
Passed. 25 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 35 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 125 passed.

python -m py_compile src/vault/documents/service.py src/vault/exceptions.py \
  tests/test_document_fact_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0005_create_document_facts as head. No Step 22
migration was added.

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

Definition of done:

* Document facts creation service exists.
* Service creates a `DocumentFact` record.
* Service validates required fact fields.
* Service rejects blank required strings.
* Service rejects malformed currency.
* Service rejects non-positive amounts.
* Service trims simple metadata strings.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* Duplicate facts are still allowed.
* Fact listing helper exists.
* Fact detail helper exists.
* Required fact helper exists.
* Fact lookup is scoped by document ID and fact ID.
* Facts from another document are not leaked.
* No facts API route is added yet.
* No file parsing is added yet.
* No control flags are added yet.
* No duplicate detection is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover creation, validation, optional fields, duplicate allowance,
  listing, scoped lookup, and safe not-found behavior.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document facts service
```


### Step 23 — Document facts API route

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped document facts API routes that allow
  owners and reviewers to create facts for an existing organization-scoped
  document, and allow owners, reviewers, and viewers to list/read safe fact
  metadata.

Completed work:

* Added `DocumentFactCreateRequest` in `src/vault/documents/schemas.py`.
* Added `DocumentFactResponse` in `src/vault/documents/schemas.py`.
* Added `POST /organizations/{organization_id}/documents/{document_id}/facts`.
* Added `GET /organizations/{organization_id}/documents/{document_id}/facts`.
* Added
  `GET /organizations/{organization_id}/documents/{document_id}/facts/{fact_id}`.
* Reused the existing documents router.
* Fact creation requires authentication and organization membership.
* Fact creation explicitly allows owners and reviewers.
* Fact creation rejects viewers and non-members.
* Fact list and detail routes require authentication and organization
  membership.
* Fact list and detail routes explicitly allow owners, reviewers, and viewers.
* Fact list and detail routes reject non-members.
* Unknown organizations keep the existing safe HTTP 403 organization-access
  behavior.
* Missing, invalid, expired, unknown-user, and inactive-user tokens continue to
  return HTTP 401.
* Fact routes verify the path document belongs to the path organization before
  creating, listing, or reading facts.
* Documents from another organization are not accepted through fact routes.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Fact creation calls `create_document_fact()`.
* Fact listing calls `list_document_facts()`.
* Fact detail calls `require_document_fact()`.
* Successful fact creation commits and refreshes the created fact before
  returning.
* Fact validation errors return HTTP 400 with safe public messages.
* Missing fact detail returns HTTP 404 with a safe public message.
* Fact responses return safe metadata only.
* Fact responses do not expose local absolute paths, raw passwords, password
  hashes, or token internals.
* Duplicate facts are still allowed.
* No database migrations were added.
* No file parsing, CSV fact import, control flags, duplicate detection, review
  decisions, document status transitions, audit logging, exports, sample
  outputs, CI files, local databases, or application container were added.
* Added `tests/test_document_facts_api.py`.

Files created or edited:

```text
src/vault/api/routes/documents.py
src/vault/documents/schemas.py
tests/test_document_facts_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_document_facts_api.py -q
python -m pytest -q
python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
python -m pytest tests/test_document_upload_api.py -q
python -m pytest tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/documents/service.py \
  src/vault/exceptions.py tests/test_document_facts_api.py \
  tests/test_document_fact_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_document_facts_api.py -q
Passed. 40 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
Passed. 65 passed.

python -m pytest tests/test_document_service.py tests/test_document_read_api.py -q
Passed. 62 passed.

python -m pytest tests/test_document_upload_api.py -q
Passed. 22 passed.

python -m pytest tests/test_document_storage.py -q
Passed. 25 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 35 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 125 passed.

python -m py_compile src/vault/api/routes/documents.py \
  src/vault/documents/schemas.py src/vault/documents/service.py \
  src/vault/exceptions.py tests/test_document_facts_api.py \
  tests/test_document_fact_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0005_create_document_facts as head. No Step 23
migration was added.

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

Definition of done:

* `POST /organizations/{organization_id}/documents/{document_id}/facts` exists.
* `GET /organizations/{organization_id}/documents/{document_id}/facts` exists.
* `GET /organizations/{organization_id}/documents/{document_id}/facts/{fact_id}`
  exists.
* Fact routes require authentication.
* Fact routes require organization membership.
* Owners can create/list/read facts.
* Reviewers can create/list/read facts.
* Viewers can list/read facts.
* Viewers cannot create facts.
* Non-members cannot create/list/read facts.
* Missing/invalid/expired tokens return authentication errors.
* Fact creation validates fact input.
* Fact creation persists a `DocumentFact` row.
* Fact listing is scoped to the requested document.
* Fact detail lookup is scoped by document ID and fact ID.
* Documents from other organizations cannot be used through fact routes.
* Facts from other documents are not leaked.
* Missing documents return safe not-found behavior.
* Missing facts return safe not-found behavior.
* Responses return safe fact metadata.
* Responses do not expose absolute local paths.
* Responses do not expose raw passwords.
* Responses do not expose password hashes.
* Routes appear in OpenAPI.
* Duplicate facts are still allowed.
* No file parsing is added yet.
* No control flags are added yet.
* No duplicate detection is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover successful fact creation, role behavior, auth failure, validation
  failure, organization scoping, document scoping, fact scoping, safe
  responses, and OpenAPI inclusion.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add document facts API route
```

### Step 24 — Control flags model and migration

Status: Complete with documented environment limitations.

Goal:

* Add the initial `ControlFlag` SQLAlchemy model and one Alembic migration that
  creates the `control_flags` table, without adding control flag generation
  service or API behavior yet.

Completed work:

* Added `src/vault/controls/__init__.py`.
* Added `src/vault/controls/severities.py`.
* Added official control flag severity values: `info`, `warning`, and
  `blocker`.
* Added `src/vault/controls/types.py`.
* Added initial official control flag type values:
  `missing_invoice_number`, `missing_invoice_date`, `missing_due_date`,
  `non_usd_currency`, `high_amount`, `duplicate_file_hash`, and
  `duplicate_invoice_attributes`.
* Added `src/vault/controls/models.py`.
* Added a typed SQLAlchemy 2-style `ControlFlag` ORM model.
* Added the official control flag fields: `id`, `document_id`, `flag_type`,
  `severity`, `reason`, and `created_at`.
* Used UUID primary keys for control flags.
* Used the existing UTC-aware timestamp helper for `created_at`.
* Added a non-null foreign key from `control_flags.document_id` to
  `documents.id`.
* Kept `document_id`, `flag_type`, `severity`, `reason`, and `created_at`
  required.
* Added reasonable string lengths for flag type, severity, and reason.
* Added a check constraint for the official severity values.
* Added a check constraint for the initial official flag type values.
* Added lookup indexes for `document_id`, `severity`, and `flag_type`.
* Added a non-unique composite index on `document_id` and `severity` for future
  review queues.
* Did not add a uniqueness constraint, so duplicate control flags remain
  allowed.
* Updated `src/vault/models.py` so shared model metadata imports
  `ControlFlag`.
* Added `alembic/versions/0006_create_control_flags.py`.
* The migration creates only the `control_flags` table and supporting indexes.
* The migration downgrade drops only the supporting indexes and
  `control_flags` table.
* Added `tests/test_control_flag_model.py`.
* Updated `tests/test_alembic_config.py` for the new migration file and
  Alembic target metadata.
* Existing Step 1 through Step 23 behavior remains compatible in the tested
  groups.
* No control flag generation service, control flag API route, duplicate
  document detection, duplicate invoice detection, review decisions, document
  status transitions, audit logging, exports, sample output, CI files, local
  databases, or application container were added.

Files created or edited:

```text
src/vault/controls/__init__.py
src/vault/controls/models.py
src/vault/controls/severities.py
src/vault/controls/types.py
src/vault/models.py
alembic/versions/0006_create_control_flags.py
tests/test_control_flag_model.py
tests/test_alembic_config.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_control_flag_model.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_control_flag_model.py \
  tests/test_document_fact_service.py tests/test_document_fact_model.py \
  tests/test_document_model.py -q
python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py tests/test_document_facts_api.py -q
python -m py_compile src/vault/controls/__init__.py \
  src/vault/controls/models.py src/vault/controls/severities.py \
  src/vault/controls/types.py src/vault/models.py \
  alembic/versions/0006_create_control_flags.py \
  tests/test_control_flag_model.py tests/test_alembic_config.py
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
python -m pytest tests/test_control_flag_model.py tests/test_alembic_config.py -q
Passed. 38 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_control_flag_model.py \
  tests/test_document_fact_service.py tests/test_document_fact_model.py \
  tests/test_document_model.py -q
Passed. 79 passed.

python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
Passed. 109 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 38 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py tests/test_document_facts_api.py -q
Passed. 165 passed.

python -m py_compile src/vault/controls/__init__.py \
  src/vault/controls/models.py src/vault/controls/severities.py \
  src/vault/controls/types.py src/vault/models.py \
  alembic/versions/0006_create_control_flags.py \
  tests/test_control_flag_model.py tests/test_alembic_config.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0006_create_control_flags as head.

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

Definition of done:

* `ControlFlag` ORM model exists.
* `control_flags` table metadata matches Project State fields.
* `document_id` links flags to documents.
* Required flag fields are non-null.
* Official severity values are defined.
* Initial official flag type values are defined.
* Severity constraint exists.
* Flag type constraint exists.
* Useful lookup indexes exist.
* Duplicate flags are still allowed.
* Shared model metadata includes `control_flags`.
* Alembic target metadata includes `control_flags`.
* Migration `0006_create_control_flags.py` exists.
* Migration creates only `control_flags` and supporting indexes.
* Migration downgrade drops only `control_flags` and supporting indexes.
* No control flag service is added yet.
* No control flag API route is added yet.
* No duplicate detection is added yet.
* No review workflow is added yet.
* No audit logging is added yet.
* No exports are added yet.
* Tests cover model structure, official values, constraints, indexes, metadata,
  and migration presence.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add control flags model
```


### Step 25 — Control flags service

Status: Complete with documented environment limitations.

Goal:

* Add a directly testable control flags service that can create, validate, list,
  retrieve, and generate initial accounting-control flags for a document using
  existing document facts, without adding API routes yet.

Completed work:

* Added `src/vault/controls/service.py`.
* Added `ControlFlagValidationError` in `src/vault/exceptions.py`.
* Added `ControlFlagNotFoundError` in `src/vault/exceptions.py`.
* Added typed `create_control_flag()` service behavior.
* The service accepts a SQLAlchemy `Session`, document ID, flag type, severity,
  and reason.
* The service creates a `ControlFlag` record and adds it to the supplied
  session.
* The service flushes so generated flag IDs are available.
* The service does not commit automatically.
* Flag type, severity, and reason are trimmed.
* Blank flag type, blank severity, and blank reason are rejected.
* Unsupported flag types are rejected using the official Step 24 flag type
  values.
* Unsupported severities are rejected using the official Step 24 severity
  values.
* Duplicate control flags are allowed for now.
* Added typed `list_control_flags()` helper.
* Flag listing is scoped to one document ID.
* Flag listing is deterministic: blocker before warning before info, then
  oldest first by `created_at`, then by `id`.
* Added typed `get_control_flag()` helper.
* Flag detail lookup scopes by both document ID and flag ID.
* Added typed `require_control_flag()` helper.
* Missing required flag lookup raises a safe custom not-found exception.
* Flags from another document are not returned by scoped lookup.
* Added typed `generate_control_flags_for_document()` helper.
* Generation inspects facts for the requested document only.
* Generation creates warning flags for missing invoice numbers.
* Generation creates warning flags for missing invoice dates.
* Generation creates info flags for missing due dates.
* Generation creates warning flags for non-USD currency.
* Generation creates blocker flags for amounts greater than or equal to 100,000
  cents.
* Generated reasons are clear, non-blank, and human-readable.
* Generation returns the created `ControlFlag` records.
* Generation flushes created flags so IDs are available.
* Generation does not commit automatically.
* Generation creates no flags when no facts exist for the document.
* Generation creates no flags for clean facts.
* Generation only inspects facts for the requested document.
* Generation does not create duplicate-file-hash flags yet.
* Generation does not create duplicate-invoice-attributes flags yet.
* Generation does not update document status.
* Generation does not verify organization membership.
* No database migrations were added.
* No control flag API routes, duplicate document detection, duplicate invoice
  detection, review decisions, document status transitions, audit logging,
  exports, sample outputs, CI files, local databases, or application container
  were added.
* Added `tests/test_control_flag_service.py`.

Files created or edited:

```text
src/vault/controls/service.py
src/vault/exceptions.py
tests/test_control_flag_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_control_flag_service.py -q
python -m pytest tests/test_control_flag_service.py \
  tests/test_control_flag_model.py tests/test_alembic_config.py -q
python -m pytest -q
python -m pytest tests/test_control_flag_service.py \
  tests/test_control_flag_model.py tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py tests/test_document_facts_api.py -q
python -m py_compile src/vault/controls/service.py src/vault/exceptions.py \
  tests/test_control_flag_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_control_flag_service.py -q
Passed. 41 passed.

python -m pytest tests/test_control_flag_service.py \
  tests/test_control_flag_model.py tests/test_alembic_config.py -q
Passed. 79 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_control_flag_service.py \
  tests/test_control_flag_model.py tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_model.py -q
Passed. 120 passed.

python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
Passed. 109 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 38 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py tests/test_document_facts_api.py -q
Passed. 165 passed.

python -m py_compile src/vault/controls/service.py src/vault/exceptions.py \
  tests/test_control_flag_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0006_create_control_flags as head. No Step 25
migration was added.

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

Definition of done:

* Control flag creation service exists.
* Service creates a `ControlFlag` record.
* Service validates required flag fields.
* Service rejects blank required strings.
* Service rejects unsupported flag types.
* Service rejects unsupported severities.
* Service trims simple metadata strings.
* Service flushes so generated IDs are available.
* Service does not commit automatically.
* Duplicate flags are still allowed.
* Flag listing helper exists.
* Flag detail helper exists.
* Required flag helper exists.
* Flag lookup is scoped by document ID and flag ID.
* Flags from another document are not leaked.
* Initial control flag generation helper exists.
* Generation inspects document facts for one document.
* Generation creates flags for missing invoice number, missing invoice date,
  missing due date, non-USD currency, and high amount.
* Generation does not create duplicate-detection flags yet.
* Generation returns created flags.
* Generation does not commit automatically.
* No control flag API route is added yet.
* No duplicate detection behavior is added yet.
* No review workflow is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover creation, validation, duplicate allowance, listing, scoped lookup,
  generation rules, clean facts, no-fact behavior, and safe not-found behavior.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add control flags service
```

### Step 26 — Control flags API routes

Status: Complete with documented environment limitations.

Goal:

* Add authenticated, organization-scoped control flag API routes that allow
  owners and reviewers to generate control flags for an existing
  organization-scoped document, and allow owners, reviewers, and viewers to
  list/read safe control flag metadata.

Completed work:

* Added `src/vault/controls/schemas.py`.
* Added `ControlFlagResponse` as a safe response schema.
* Control flag responses include `id`, `document_id`, `flag_type`, `severity`,
  `reason`, and `created_at`.
* Control flag responses do not include local absolute file paths, raw
  passwords, password hashes, or token internals.
* Reused the existing documents router in `src/vault/api/routes/documents.py`.
* Added
  `POST /organizations/{organization_id}/documents/{document_id}/control-flags/generate`.
* The generation route returns HTTP 200 consistently, including when no flags
  are generated.
* Added
  `GET /organizations/{organization_id}/documents/{document_id}/control-flags`.
* Added
  `GET /organizations/{organization_id}/documents/{document_id}/control-flags/{flag_id}`.
* All control flag routes require authentication.
* All control flag routes require organization membership through
  `require_organization_roles()`.
* Control flag generation explicitly allows owners and reviewers.
* Viewers cannot generate control flags.
* Control flag list and detail routes explicitly allow owners, reviewers, and
  viewers.
* Non-members cannot generate, list, or read control flags.
* Missing, invalid, expired, unknown-user, and inactive-user tokens continue to
  return HTTP 401.
* Unknown organizations continue to return the existing safe HTTP 403
  organization-access behavior.
* Control flag routes verify the path document belongs to the path organization
  before generating, listing, or reading flags.
* Documents from another organization are rejected with safe HTTP 404 behavior
  when accessed through an otherwise accessible organization path.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* Control flag generation calls `generate_control_flags_for_document()`.
* Control flag listing calls `list_control_flags()`.
* Control flag detail calls `require_control_flag()`.
* Successful control flag generation commits and refreshes generated flags
  before returning.
* Generated rows store document ID, flag type, severity, reason, ID, and
  created timestamp.
* Control flag listing is scoped to the requested document.
* Control flag detail lookup is scoped by document ID and flag ID.
* Missing control flag detail returns HTTP 404 with a safe public message.
* Flags from other documents or organizations are not leaked.
* Duplicate-file-hash flags are not generated yet.
* Duplicate-invoice-attributes flags are not generated yet.
* No database migrations were added.
* No duplicate detection behavior, review workflow, document status
  transitions, audit logging, exports, sample outputs, CI files, local
  databases, or application container were added.
* Added `tests/test_control_flags_api.py`.

Files created or edited:

```text
src/vault/api/routes/documents.py
src/vault/controls/schemas.py
src/vault/exceptions.py
tests/test_control_flags_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_control_flags_api.py -q
python -m pytest tests/test_control_flags_api.py \
  tests/test_control_flag_service.py tests/test_control_flag_model.py \
  tests/test_document_facts_api.py -q
python -m pytest -q
python -m pytest tests/test_control_flags_api.py \
  tests/test_control_flag_service.py tests/test_control_flag_model.py \
  tests/test_alembic_config.py -q
python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_facts_api.py \
  tests/test_document_model.py -q
python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py \
  src/vault/controls/schemas.py src/vault/exceptions.py \
  tests/test_control_flags_api.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_control_flags_api.py -q
Passed. 42 passed.

python -m pytest tests/test_control_flags_api.py \
  tests/test_control_flag_service.py tests/test_control_flag_model.py \
  tests/test_document_facts_api.py -q
Passed. 137 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

python -m pytest tests/test_control_flags_api.py \
  tests/test_control_flag_service.py tests/test_control_flag_model.py \
  tests/test_alembic_config.py -q
Passed. 121 passed.

python -m pytest tests/test_document_fact_service.py \
  tests/test_document_fact_model.py tests/test_document_facts_api.py \
  tests/test_document_model.py -q
Passed. 105 passed.

python -m pytest tests/test_document_service.py tests/test_document_read_api.py \
  tests/test_document_upload_api.py tests/test_document_storage.py -q
Passed. 109 passed.

python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py tests/test_package_import.py -q
Passed. 38 passed.

python -m pytest tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py \
  tests/test_auth_tokens.py tests/test_current_user_dependency.py -q
Passed. 51 passed.

python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py tests/test_organization_service.py \
  tests/test_passwords.py tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
Passed. 125 passed.

python -m py_compile src/vault/api/routes/documents.py \
  src/vault/controls/schemas.py src/vault/exceptions.py \
  tests/test_control_flags_api.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0006_create_control_flags as head. No Step 26
migration was added.

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

Definition of done:

* Control flag response schema exists.
* Control flag generate, list, and detail routes exist.
* Control flag routes require authentication.
* Control flag routes require organization membership.
* Owners can generate/list/read control flags.
* Reviewers can generate/list/read control flags.
* Viewers can list/read control flags.
* Viewers cannot generate control flags.
* Non-members cannot generate/list/read control flags.
* Missing/invalid/expired tokens return authentication errors.
* Control flag generation verifies the document belongs to the organization.
* Control flag generation persists generated flags.
* Control flag generation returns safe flag metadata.
* Control flag listing is scoped to the requested document.
* Control flag detail lookup is scoped by document ID and flag ID.
* Documents from other organizations cannot be used through control flag routes.
* Flags from other documents are not leaked.
* Missing documents return safe not-found behavior.
* Missing flags return safe not-found behavior.
* Responses do not expose absolute local paths.
* Responses do not expose raw passwords.
* Responses do not expose password hashes.
* Routes appear in OpenAPI.
* Duplicate-file-hash flags are not generated yet.
* Duplicate-invoice-attributes flags are not generated yet.
* No duplicate detection behavior is added yet.
* No review workflow is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover successful generation, role behavior, auth failure, organization
  scoping, document scoping, flag scoping, safe responses, and OpenAPI
  inclusion.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add control flags API routes
```



### Step 27 — Duplicate detection service

Status: Complete with documented environment limitations.

Goal:

* Add directly testable duplicate detection service behavior that identifies
  duplicate documents by SHA-256 file hash and duplicate invoice facts by
  vendor, invoice number, and amount, then creates duplicate-oriented control
  flags without adding API routes yet.

Completed work:

* Added typed `find_duplicate_documents_by_hash()` in
  `src/vault/controls/service.py`.
* The file-hash helper loads the target document and returns other documents in
  the same organization with the same SHA-256 hash.
* The file-hash helper excludes the target document itself.
* The file-hash helper does not return documents from other organizations.
* The file-hash helper returns an empty list when the target document is
  missing or when no same-organization matches exist.
* Added typed `find_duplicate_invoice_facts()` in
  `src/vault/controls/service.py`.
* The invoice duplicate helper inspects facts on the requested document.
* The invoice duplicate helper compares against facts on other documents in the
  same organization only.
* Duplicate invoice matching uses same normalized vendor name, same non-blank
  invoice number, and same amount cents.
* Vendor matching is case-insensitive.
* Invoice numbers are treated as exact after stored service trimming.
* Facts with missing or blank invoice numbers are ignored.
* Facts on the same document are excluded from duplicate invoice results.
* Facts from other organizations are not leaked.
* Added typed `generate_duplicate_control_flags_for_document()`.
* Duplicate file-hash generation creates one `duplicate_file_hash` flag when
  same-organization documents share the target document SHA-256 hash.
* Duplicate file-hash flags use blocker severity.
* Duplicate invoice-attribute generation creates one
  `duplicate_invoice_attributes` flag when same-organization facts match by
  vendor, invoice number, and amount cents.
* Duplicate invoice-attribute flags use warning severity.
* Generated duplicate reasons are human-readable and mention file hash or
  vendor/invoice/amount as the duplicate basis.
* Generated duplicate reasons do not expose local absolute stored paths.
* Duplicate generation uses the existing `create_control_flag()` helper.
* Duplicate generation returns created `ControlFlag` records and flushes so IDs
  are available.
* Duplicate generation does not commit automatically.
* Duplicate generation creates no flags when no duplicates are found.
* Duplicate generation does not inspect or flag cross-organization duplicates.
* Duplicate generation does not update document status.
* Duplicate duplicate-detection flags may still be generated if the helper is
  called repeatedly; deduplication is deferred.
* Organization membership verification remains outside this service and will be
  enforced by future route dependencies.
* No database migrations were added.
* No duplicate detection API routes, review decisions, audit logging, exports,
  sample outputs, CI files, local databases, or uploaded files were added.

Files created or edited:

```text
src/vault/controls/service.py
tests/test_duplicate_detection_service.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_duplicate_detection_service.py -q
python -m pytest tests/test_duplicate_detection_service.py \
  tests/test_control_flag_service.py -q
python -m pytest -q
python -m pytest tests/test_control_flags_api.py \
  tests/test_duplicate_detection_service.py -q
python -m pytest tests/test_control_flag_service.py \
  tests/test_control_flag_model.py tests/test_document_fact_service.py -q
python -m pytest tests/test_document_fact_model.py \
  tests/test_document_facts_api.py tests/test_document_model.py -q
python -m pytest tests/test_document_service.py \
  tests/test_document_read_api.py -q
python -m pytest tests/test_document_upload_api.py \
  tests/test_document_storage.py -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_config.py tests/test_database_config.py \
  tests/test_package_import.py -q
python -m pytest tests/test_auth_login_api.py \
  tests/test_auth_login_service.py tests/test_auth_me_api.py \
  tests/test_auth_registration_api.py tests/test_auth_tokens.py \
  tests/test_current_user_dependency.py -q
python -m pytest tests/test_organization_access_service.py \
  tests/test_organization_create_api.py tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py tests/test_passwords.py \
  tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/controls/service.py \
  tests/test_duplicate_detection_service.py
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
python -m pytest tests/test_duplicate_detection_service.py -q
Passed. 24 passed.

python -m pytest tests/test_duplicate_detection_service.py \
  tests/test_control_flag_service.py -q
Passed. 65 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was then run in smaller groups.

Smaller pytest groups passed:

* control flags API plus duplicate detection service: 66 passed
* control flag service/model plus document fact service: 93 passed
* document fact model/API plus document model: 67 passed
* document service/read API: 62 passed
* document upload API/storage: 47 passed
* Alembic/API health/config/package smoke group: 38 passed
* auth/current-user group: 51 passed
* organization access/create/models/RBAC group: 70 passed
* organization service/passwords/upload validation/user group: 55 passed

python -m py_compile src/vault/controls/service.py \
  tests/test_duplicate_detection_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0006_create_control_flags as head. No Step 27
migration was added.

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

Definition of done:

* Duplicate file-hash lookup helper exists.
* Duplicate invoice-attribute lookup helper exists.
* Duplicate detection is scoped to the target document's organization.
* Duplicate detection excludes the target document where appropriate.
* Duplicate detection does not leak cross-organization data.
* Duplicate invoice detection uses vendor, invoice number, and amount.
* Duplicate invoice detection ignores missing invoice numbers.
* Duplicate control flag generation helper exists.
* Duplicate generation creates duplicate-file-hash flags.
* Duplicate generation creates duplicate-invoice-attributes flags.
* Duplicate generated flags use official flag types.
* Duplicate generated flags use official severities.
* Duplicate generated reasons are clear and safe.
* Duplicate generation returns created flags.
* Duplicate generation flushes so IDs are available.
* Duplicate generation does not commit automatically.
* Duplicate generation creates no flags when no duplicates exist.
* Duplicate generation does not update document status.
* No duplicate detection API route is added yet.
* No review workflow is added yet.
* No audit logging is added yet.
* No exports are added yet.
* No migrations are added in this step.
* Tests cover duplicate document lookup, duplicate fact lookup, organization
  scoping, generated duplicate flags, clean/no-match behavior, and safe
  reasons.
* Existing tests were validated in smaller groups due to sandbox timeout.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add duplicate detection service
```




### Step 28 — Duplicate detection API route

Status: Complete with documented environment limitations.

Goal:

* Add an authenticated, organization-scoped duplicate detection API route that
  lets owners and reviewers generate duplicate-oriented control flags for an
  existing organization-scoped document.

Completed work:

* Added `POST /organizations/{organization_id}/documents/{document_id}/duplicates/generate`.
* Reused the existing documents router.
* Reused the safe `ControlFlagResponse` schema.
* The route requires authentication.
* The route requires organization membership through
  `require_organization_roles()`.
* The route explicitly allows owners and reviewers.
* The route rejects viewers, non-members, and unknown organizations.
* Missing, invalid, expired, unknown-user, and inactive-user tokens return
  HTTP 401 before duplicate generation runs.
* The route verifies the path document belongs to the path organization with
  `require_document_for_organization()`.
* Documents from other organizations are rejected with safe not-found behavior.
* Missing documents in an accessible organization return HTTP 404 with a safe
  public message.
* The route calls `generate_duplicate_control_flags_for_document()`.
* Successful duplicate generation commits and refreshes generated flags before
  returning.
* Successful duplicate generation returns HTTP 200.
* Generation returns an empty list when no duplicate flags are generated.
* Responses include safe control flag metadata only: `id`, `document_id`,
  `flag_type`, `severity`, `reason`, and `created_at`.
* Responses do not expose local absolute file paths, raw passwords, password
  hashes, or token internals.
* Duplicate generated reasons do not expose local stored file paths.
* Added `tests/test_duplicate_detection_api.py`.
* Tests cover owner and reviewer success, viewer denial, non-member denial,
  token failures, unknown organization behavior, document scoping, missing
  documents, duplicate file hash flags, duplicate invoice attribute flags,
  official severities, persistence, safe response metadata, cross-organization
  duplicate leak prevention, empty generation, and OpenAPI inclusion.
* No database migrations were added.
* No review workflow, audit logging, exports, sample output, CI files, local
  databases, or application container were added.

Files created or edited:

```text
src/vault/api/routes/documents.py
tests/test_duplicate_detection_api.py
docs/Project_State.md
```

Commands run:

```bash
python -m pytest tests/test_duplicate_detection_api.py -q
python -m pytest tests/test_duplicate_detection_api.py \
  tests/test_duplicate_detection_service.py -q
python -m pytest tests/test_control_flags_api.py -q
python -m pytest -q
python -m pytest tests/test_alembic_config.py tests/test_api_health.py \
  tests/test_auth_login_api.py tests/test_auth_login_service.py \
  tests/test_auth_me_api.py tests/test_auth_registration_api.py -q
python -m pytest tests/test_auth_tokens.py tests/test_config.py \
  tests/test_control_flag_model.py tests/test_control_flag_service.py \
  tests/test_control_flags_api.py tests/test_current_user_dependency.py -q
python -m pytest tests/test_database_config.py \
  tests/test_document_fact_model.py tests/test_document_fact_service.py -q
python -m pytest tests/test_document_facts_api.py -q
python -m pytest tests/test_document_model.py \
  tests/test_document_read_api.py -q
python -m pytest tests/test_document_service.py \
  tests/test_document_storage.py tests/test_document_upload_api.py -q
python -m pytest tests/test_duplicate_detection_api.py \
  tests/test_duplicate_detection_service.py \
  tests/test_organization_access_service.py -q
python -m pytest tests/test_organization_create_api.py \
  tests/test_organization_models.py \
  tests/test_organization_rbac_dependency.py -q
python -m pytest tests/test_organization_service.py \
  tests/test_package_import.py tests/test_passwords.py -q
python -m pytest tests/test_upload_validation.py tests/test_user_model.py \
  tests/test_user_service.py -q
python -m py_compile src/vault/api/routes/documents.py \
  src/vault/controls/service.py src/vault/controls/schemas.py \
  src/vault/exceptions.py tests/test_duplicate_detection_api.py \
  tests/test_duplicate_detection_service.py
python scripts/run_vault.py --help
python -m alembic history
python -m ruff check .
python -m mypy src scripts tests
python -m bandit -r src
python -m pip_audit
git status --short
docker --version
```

Validation results:

```text
python -m pytest tests/test_duplicate_detection_api.py -q
Passed. 32 passed.

python -m pytest tests/test_duplicate_detection_api.py \
  tests/test_duplicate_detection_service.py -q
Passed. 56 passed.

python -m pytest tests/test_control_flags_api.py -q
Passed. 42 passed.

python -m pytest -q
Attempted. The sandbox command timed out after mid-suite progress, not after a
reported test failure. The suite was run in smaller groups.

The smaller pytest groups listed above passed.

python -m py_compile src/vault/api/routes/documents.py \
  src/vault/controls/service.py src/vault/controls/schemas.py \
  src/vault/exceptions.py tests/test_duplicate_detection_api.py \
  tests/test_duplicate_detection_service.py
Passed.

python scripts/run_vault.py --help
Passed. Help text displayed.

python -m alembic history
Passed. Alembic history shows 0006_create_control_flags as head. No Step 28
migration was added.

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

Definition of done:

* Duplicate detection API route exists.
* Route requires authentication.
* Route requires organization membership.
* Owners can generate duplicate flags.
* Reviewers can generate duplicate flags.
* Viewers cannot generate duplicate flags.
* Non-members cannot generate duplicate flags.
* Missing, invalid, expired, unknown-user, and inactive-user tokens return
  authentication errors.
* Route verifies the document belongs to the organization.
* Documents from other organizations cannot be used through the route.
* Missing documents return safe not-found behavior.
* Route calls the Step 27 duplicate detection service.
* Route commits successful duplicate flag generation.
* Route returns generated duplicate control flags.
* Route returns an empty list when no duplicate flags are generated.
* Responses return safe control flag metadata.
* Responses do not expose absolute local paths.
* Responses do not expose raw passwords.
* Responses do not expose password hashes.
* Duplicate detection does not leak cross-organization data.
* Duplicate detection route appears in OpenAPI.
* No review workflow was added.
* No audit logging was added.
* No exports were added.
* No migrations were added.
* Tests cover successful duplicate generation, role behavior, auth failure,
  organization scoping, document scoping, cross-org leak prevention, empty
  generation, safe responses, persistence, and OpenAPI inclusion.
* Existing tests were validated in smaller groups due to sandbox timeout.
* Pytest groups pass.
* CLI help works.
* Alembic history works.
* Project State is updated.
* No generated private/local files are included.

Suggested commit message:

```text
Add duplicate detection API route
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
