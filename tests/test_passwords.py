"""Tests for Vault password hashing helpers."""

from vault.auth.passwords import hash_password, verify_password


def test_hash_password_returns_string() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert isinstance(password_hash, str)


def test_hash_password_does_not_return_raw_password() -> None:
    raw_password = "correct horse battery staple"

    password_hash = hash_password(raw_password)

    assert password_hash != raw_password


def test_verify_password_succeeds_for_correct_password() -> None:
    raw_password = "correct horse battery staple"
    password_hash = hash_password(raw_password)

    assert verify_password(raw_password, password_hash) is True


def test_verify_password_fails_for_wrong_password() -> None:
    password_hash = hash_password("correct horse battery staple")

    assert verify_password("wrong password", password_hash) is False


def test_hashing_same_password_twice_produces_different_hashes() -> None:
    raw_password = "correct horse battery staple"

    first_hash = hash_password(raw_password)
    second_hash = hash_password(raw_password)

    assert first_hash != second_hash
