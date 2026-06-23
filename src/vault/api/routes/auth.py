"""Authentication routes for Vault."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vault.api.dependencies import get_database_session
from vault.auth.schemas import UserRegistrationRequest, UserRegistrationResponse
from vault.auth.service import create_user
from vault.exceptions import DuplicateUserError, ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    registration: UserRegistrationRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> UserRegistrationResponse:
    """Create a Vault user account and return safe user data."""
    try:
        user = create_user(
            session,
            email=registration.email,
            raw_password=registration.password,
            full_name=registration.full_name,
        )
        session.commit()
        session.refresh(user)
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        ) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return UserRegistrationResponse.model_validate(user)
