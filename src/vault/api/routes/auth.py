"""Authentication routes for Vault."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from vault.api.dependencies import get_database_session
from vault.auth.schemas import (
    UserLoginRequest,
    UserLoginResponse,
    UserRegistrationRequest,
    UserRegistrationResponse,
)
from vault.auth.service import authenticate_user, create_user
from vault.auth.tokens import create_access_token
from vault.exceptions import (
    AuthenticationError,
    DuplicateUserError,
    InactiveUserError,
    ValidationError,
)

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


@router.post(
    "/login",
    response_model=UserLoginResponse,
    status_code=status.HTTP_200_OK,
)
def login_user(
    login: UserLoginRequest,
    session: Annotated[Session, Depends(get_database_session)],
) -> UserLoginResponse:
    """Authenticate a user and return a bearer access token."""
    try:
        user = authenticate_user(
            session,
            email=login.email,
            raw_password=login.password,
        )
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid email or password.",
        ) from exc
    except (AuthenticationError, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    access_token = create_access_token(user.id)
    return UserLoginResponse(access_token=access_token)
