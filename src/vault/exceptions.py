"""Custom exceptions for Vault."""


class VaultError(Exception):
    """Base exception for Vault errors."""


class ValidationError(VaultError):
    """Raised when input values fail service validation."""


class DuplicateUserError(VaultError):
    """Raised when user creation would duplicate an email address."""
