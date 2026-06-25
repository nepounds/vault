"""Custom exceptions for Vault."""


class VaultError(Exception):
    """Base exception for Vault errors."""


class ValidationError(VaultError):
    """Raised when input values fail service validation."""


class DuplicateUserError(VaultError):
    """Raised when user creation would duplicate an email address."""


class AuthenticationError(VaultError):
    """Raised when authentication credentials or tokens are invalid."""


class InactiveUserError(AuthenticationError):
    """Raised when an inactive user attempts to authenticate."""


class OrganizationError(VaultError):
    """Base exception for organization service errors."""


class OrganizationValidationError(OrganizationError):
    """Raised when organization input fails service validation."""


class OrganizationAccessError(OrganizationError):
    """Base exception for organization access errors."""


class OrganizationMembershipRequiredError(OrganizationAccessError):
    """Raised when organization membership is required."""


class OrganizationRoleRequiredError(OrganizationAccessError):
    """Raised when an organization role is required."""

