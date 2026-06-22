"""FastAPI app factory for Vault."""

from __future__ import annotations

from fastapi import FastAPI

from vault import __version__
from vault.api.routes.health import router as health_router

APP_DESCRIPTION = (
    "Minimal Vault API shell for the secure accounting document workflow app. "
    "Current behavior is limited to health and OpenAPI endpoints; database, "
    "authentication, uploads, reviews, audit logs, and exports are planned later."
)


def create_app() -> FastAPI:
    """Create and configure the Vault FastAPI application."""
    app = FastAPI(
        title="Vault",
        description=APP_DESCRIPTION,
        version=__version__,
    )
    app.include_router(health_router)
    return app


app = create_app()
