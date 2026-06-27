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


class DocumentError(VaultError):
    """Base exception for document service errors."""


class DocumentValidationError(DocumentError):
    """Raised when document metadata fails service validation."""


class DocumentUploadValidationError(DocumentError):
    """Raised when upload metadata fails validation."""


class DocumentNotFoundError(DocumentError):
    """Raised when requested document metadata cannot be found."""


class DocumentFactValidationError(DocumentError):
    """Raised when structured document fact data fails validation."""


class DocumentFactNotFoundError(DocumentError):
    """Raised when requested document fact metadata cannot be found."""


class ControlFlagValidationError(VaultError):
    """Raised when control flag data fails service validation."""


class ControlFlagNotFoundError(VaultError):
    """Raised when requested control flag metadata cannot be found."""


class ReviewDecisionValidationError(VaultError):
    """Raised when review decision data fails service validation."""


class ReviewDecisionNotFoundError(VaultError):
    """Raised when requested review decision metadata cannot be found."""

class AuditEntryValidationError(VaultError):
    """Raised when audit entry data fails service validation."""


class AuditEntryNotFoundError(VaultError):
    """Raised when requested audit entry metadata cannot be found."""

