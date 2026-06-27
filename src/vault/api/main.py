"""FastAPI app factory for Vault."""

from __future__ import annotations

from fastapi import FastAPI

from vault import __version__
from vault.api.routes.audit import router as audit_router
from vault.api.routes.auth import router as auth_router
from vault.api.routes.documents import router as documents_router
from vault.api.routes.exports import router as exports_router
from vault.api.routes.health import router as health_router
from vault.api.routes.organizations import router as organizations_router

APP_DESCRIPTION = (
    "Minimal Vault API shell for the secure accounting document workflow app. "
    "Current behavior is limited to health, OpenAPI, registration, login, "
    "current-user lookup, organizations, uploads, document reads, reviews, "
    "organization-scoped audit reads, and CSV exports."
)


def create_app() -> FastAPI:
    """Create and configure the Vault FastAPI application."""
    app = FastAPI(
        title="Vault",
        description=APP_DESCRIPTION,
        version=__version__,
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(organizations_router)
    app.include_router(documents_router)
    app.include_router(audit_router)
    app.include_router(exports_router)
    return app


app = create_app()
