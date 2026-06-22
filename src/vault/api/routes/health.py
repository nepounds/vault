"""Health-check route for the Vault API shell."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Response body returned by the health endpoint."""

    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
def read_health() -> HealthResponse:
    """Return a small health-check response."""
    return HealthResponse(status="ok", service="vault")
