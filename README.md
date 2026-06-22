# Vault

Vault is a secure accounting document workflow app for small-business finance teams.

It handles finance document intake, validation, review, approval, audit logging, and export. The project is designed as the next step after local-first accounting/reporting tools by moving the workflow online with authentication, authorization, database migrations, file-upload safety, and security-focused testing.

> Status: Planning only. No implementation has been completed yet.

## Portfolio summary

Vault is a FastAPI and PostgreSQL finance workflow app with user authentication, role-based access control, secure document upload validation, review queues, immutable audit logging, and exportable accounting reports.

Resume version:

> Built Vault, a secure accounting workflow web app with FastAPI, PostgreSQL, user authentication, role-based access control, document upload validation, approval workflows, audit logging, Docker Compose, CI, and security checks.

## Problem

Small businesses often handle invoices, receipts, and supporting accounting documents through email threads, shared folders, spreadsheets, and memory. That creates weak controls:

- no clear owner,
- no reliable approval history,
- no consistent validation,
- no simple audit trail,
- and no clean export of approved records.

Vault solves the portfolio-sized version of that problem using fake sample data.

## Target users

- Small-business owners
- Bookkeepers
- Staff accountants
- Finance reviewers
- Internal tool clients
- Portfolio reviewers and freelance clients

## MVP scope

The MVP will include:

1. User registration and login.
2. Password hashing.
3. Organization creation.
4. Organization membership.
5. Role-based access control for owner, reviewer, and viewer roles.
6. Secure fake document upload workflow.
7. File size, extension, MIME, and content validation.
8. Document metadata storage.
9. Review queue with pending, approved, rejected, and needs_info statuses.
10. Decision reasons for review outcomes.
11. Validation flags for common accounting-control issues.
12. Duplicate detection using file hashes and invoice attributes.
13. Immutable audit log entries for important actions.
14. CSV exports for approved documents, exceptions, and audit history.
15. A documented FastAPI interface.
16. Docker Compose for local app and PostgreSQL development.
17. CI with Ruff, mypy, pytest, Bandit, and pip-audit where practical.

## Non-goals for MVP

Vault will not include:

- real customer data,
- real bank connections,
- payment processing,
- live OCR,
- AI extraction,
- production deployment claims,
- email delivery,
- paid subscriptions,
- React frontend,
- or S3/cloud storage.

## Planned stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- passlib or pwdlib for password hashing
- pytest
- ruff
- mypy
- bandit
- pip-audit
- Docker Compose
- GitHub Actions

## Repository structure

```text
vault/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   ├── Architecture.md
│   ├── Project_State.md
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
│       ├── auth/
│       ├── documents/
│       ├── organizations/
│       ├── reviews/
│       ├── audit/
│       ├── exports/
│       ├── config.py
│       ├── database.py
│       └── exceptions.py
├── tests/
├── README.md
├── pyproject.toml
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Planned quickstart

The final quickstart should look roughly like this:

```bash
python -m venv .venv
. .venv/Scripts/activate
python -m pip install -e ".[dev]"
copy .env.example .env
docker compose up -d db
alembic upgrade head
uvicorn vault.api.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Validation commands

```bash
python -m ruff check .
python -m mypy src scripts tests
python -m pytest
python -m bandit -r src
python -m pip_audit
git status
```

If one command is not applicable during an early step, the Project State file must say why.

## Safety note

All committed examples must use fake companies, fake users, fake vendors, fake invoices, and fake uploaded files. No real financial records belong in this repository.
