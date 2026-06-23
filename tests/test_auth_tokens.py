"""Tests for Vault access token helpers."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from vault.auth.tokens import create_access_token, decode_access_token
from vault.config import VaultSettings
from vault.exceptions import AuthenticationError


def test_access_token_creation_returns_string() -> None:
    token = create_access_token(uuid4())

    assert isinstance(token, str)
    assert token != ""


def test_access_token_can_be_decoded() -> None:
    user_id = uuid4()
    token = create_access_token(user_id)

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)


def test_access_token_subject_contains_user_id() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)
    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)


def test_access_token_includes_expiration() -> None:
    token = create_access_token(uuid4())
    payload = decode_access_token(token)

    assert "exp" in payload
    assert isinstance(payload["exp"], int)


def test_expired_tokens_are_rejected() -> None:
    user_id = uuid4()
    current_time = datetime(2026, 1, 1, tzinfo=UTC)

    token = create_access_token(
        user_id,
        expires_delta=timedelta(minutes=-1),
        now=current_time,
    )

    with pytest.raises(AuthenticationError, match="expired"):
        decode_access_token(token, now=current_time)


def test_token_with_wrong_secret_is_rejected() -> None:
    user_id = uuid4()
    settings = VaultSettings(token_secret_key="first test secret")
    wrong_settings = VaultSettings(token_secret_key="second test secret")

    token = create_access_token(user_id, settings=settings)

    with pytest.raises(AuthenticationError, match="Invalid access token"):
        decode_access_token(token, settings=wrong_settings)
