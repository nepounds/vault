# Vault Step Plan

Vault was built in small, testable backend steps. The MVP is now at the final polish stage.

## Completed phases

### Phase 0 — Planning

- Step 0: planning docs, scope, architecture, and project-control rules.

### Phase 1 — Foundation

- Step 1: Python package skeleton and tooling baseline.
- Step 2: FastAPI app shell and `/health`.
- Step 3: typed database settings, SQLAlchemy helpers, and Docker Compose PostgreSQL baseline.
- Step 4: Alembic infrastructure and baseline migration.

### Phase 2 — Users, auth, and organizations

- Step 5: user model and migration.
- Step 6: password hashing and user creation service.
- Step 7: registration API route.
- Step 8: login service and token foundation.
- Step 9: current-user dependency and `GET /auth/me`.
- Step 10: organization and membership models.
- Step 11: organization creation service.
- Step 12: organization creation API route.
- Step 13: organization membership access helpers.
- Step 14: reusable organization RBAC route dependency.

### Phase 3 — Document intake

- Step 15: document model and status values.
- Step 16: document metadata service.
- Step 17: upload validation helpers.
- Step 18: local file storage and SHA-256 helpers.
- Step 19: authenticated organization-scoped document upload.
- Step 20: authenticated organization-scoped document reads.
- Step 21: document facts model and migration.
- Step 22: document facts service.
- Step 23: document facts API routes.

### Phase 4 — Controls and review workflow

- Step 24: control flag values, model, and migration.
- Step 25: control flag service behavior.
- Step 26: control flag API routes.
- Step 27: duplicate detection service behavior.
- Step 28: duplicate detection API route.
- Step 29: review decision model and migration.
- Step 30: review decision service and document status transitions.
- Step 31: review decision API routes.

### Phase 5 — Audit and exports

- Step 32: audit action/entity values, model, and migration.
- Step 33: audit entry service.
- Step 34: audit entry creation wired into state-changing API workflows.
- Step 35: audit list/detail API routes.
- Step 36: CSV export builders and database-backed row helpers.
- Step 37: authenticated organization-scoped export API routes.
- Step 38: fake sample input/output and demo export command.

### Phase 6 — CI, docs, and final hardening

- Step 39: CI workflow, honest README quickstart, final validation, and MVP completion status.

## Current status

Step 39 is the final MVP polish step. It does not add new product behavior. It adds CI, updates documentation to match implemented behavior, regenerates deterministic sample output, and records final validation results.

## Post-MVP backlog

Possible later work:

- watch the first GitHub Actions runs and fix any environment-only CI issues;
- add a small dashboard or screenshots;
- add member invitation and membership-management routes;
- add document download routes;
- add refresh tokens and password reset;
- add rate limiting and stronger production auth hardening;
- add OCR or AI extraction only after the backend workflow remains stable;
- add cloud storage only after deployment is intentionally scoped.

## Standard validation commands

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
git status
```

Smoke checks:

```bash
python scripts/run_vault.py --help
python scripts/run_vault.py export-demo --output-dir examples/sample_output
python -m alembic history
```

Optional Docker-backed migration smoke check:

```bash
docker compose up -d db
python -m alembic upgrade head
python -m alembic current
docker compose down
```

## Final MVP definition of done

- CI workflow exists and runs Ruff, mypy, pytest, Bandit, and pip-audit.
- README is current and does not claim unimplemented behavior.
- Architecture and step docs are not materially stale.
- Demo sample outputs regenerate deterministically.
- Sample outputs remain fake and safe.
- Ruff, mypy, pytest, Bandit, and pip-audit pass locally or failures are documented honestly.
- CLI help works.
- Demo export command works.
- Alembic history works.
- Docker-backed migration check is run or clearly skipped.
- Project State marks the MVP complete only after validation supports it.

Suggested Step 39 commit:

```text
Add CI and final README polish
```
