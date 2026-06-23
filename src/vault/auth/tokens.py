"""Access token helpers for Vault authentication."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any, Literal, TypedDict
from uuid import UUID

from vault.config import VaultSettings, load_settings
from vault.exceptions import AuthenticationError

_SUPPORTED_ALGORITHM: Literal["HS256"] = "HS256"


class AccessTokenPayload(TypedDict):
    """Validated access-token claims used by Vault."""

    sub: str
    exp: int


class _TokenHeader(TypedDict):
    alg: str
    typ: str


def create_access_token(
    user_id: UUID,
    *,
    settings: VaultSettings | None = None,
    expires_delta: timedelta | None = None,
    now: datetime | None = None,
) -> str:
    """Create a signed bearer access token for a user."""
    active_settings = load_settings() if settings is None else settings
    _validate_algorithm(active_settings.token_algorithm)

    current_time = _ensure_utc(now or datetime.now(UTC))
    token_lifetime = expires_delta or timedelta(
        minutes=active_settings.access_token_expiration_minutes
    )
    expires_at = current_time + token_lifetime
    header: _TokenHeader = {"alg": active_settings.token_algorithm, "typ": "JWT"}
    payload: AccessTokenPayload = {
        "sub": str(user_id),
        "exp": int(expires_at.timestamp()),
    }

    signing_input = _encode_json(header) + "." + _encode_json(payload)
    signature = _sign(signing_input, active_settings.token_secret_key)
    return signing_input + "." + signature


def decode_access_token(
    token: str,
    *,
    settings: VaultSettings | None = None,
    now: datetime | None = None,
) -> AccessTokenPayload:
    """Validate a signed access token and return its claims."""
    active_settings = load_settings() if settings is None else settings
    _validate_algorithm(active_settings.token_algorithm)

    header_text, payload_text, signature = _split_token(token)
    signing_input = header_text + "." + payload_text
    expected_signature = _sign(signing_input, active_settings.token_secret_key)
    if not hmac.compare_digest(signature, expected_signature):
        raise AuthenticationError("Invalid access token.")

    header = _decode_json(header_text)
    if header.get("alg") != active_settings.token_algorithm:
        raise AuthenticationError("Invalid access token.")
    if header.get("typ") != "JWT":
        raise AuthenticationError("Invalid access token.")

    payload = _decode_json(payload_text)
    subject = payload.get("sub")
    expiration = payload.get("exp")
    if not isinstance(subject, str) or subject == "":
        raise AuthenticationError("Invalid access token.")
    if not isinstance(expiration, int):
        raise AuthenticationError("Invalid access token.")

    current_time = _ensure_utc(now or datetime.now(UTC))
    if expiration <= int(current_time.timestamp()):
        raise AuthenticationError("Access token has expired.")

    return {"sub": subject, "exp": expiration}


def _validate_algorithm(algorithm: str) -> None:
    if algorithm != _SUPPORTED_ALGORITHM:
        raise AuthenticationError("Unsupported token algorithm.")


def _split_token(token: str) -> tuple[str, str, str]:
    parts = token.split(".")
    if len(parts) != 3:
        raise AuthenticationError("Invalid access token.")
    return parts[0], parts[1], parts[2]


def _encode_json(value: _TokenHeader | AccessTokenPayload) -> str:
    raw_json = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return _base64url_encode(raw_json)


def _decode_json(value: str) -> dict[str, Any]:
    try:
        raw_json = _base64url_decode(value)
        decoded = json.loads(raw_json)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuthenticationError("Invalid access token.") from exc
    if not isinstance(decoded, dict):
        raise AuthenticationError("Invalid access token.")
    return decoded


def _sign(signing_input: str, secret_key: str) -> str:
    signature = hmac.new(
        secret_key.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(signature)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
