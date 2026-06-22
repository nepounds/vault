"""Tests for the minimal FastAPI application shell."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vault.api.main import create_app


def test_create_app_returns_fastapi_instance() -> None:
    """The app factory returns a FastAPI application."""
    app = create_app()

    assert isinstance(app, FastAPI)


def test_health_endpoint_returns_ok_response() -> None:
    """The health endpoint returns a stable JSON response."""
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "vault"}


def test_openapi_schema_is_reachable() -> None:
    """The FastAPI OpenAPI schema is available without a server."""
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Vault"
