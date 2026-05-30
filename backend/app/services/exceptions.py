"""Domain-layer exceptions.

These are raised by services and translated to HTTPException by routers.
"""


class DomainError(Exception):
    """Base exception for all domain-level errors."""


class NotFoundError(DomainError):
    """Entity not found → HTTP 404."""


class ConflictError(DomainError):
    """Duplicate or conflicting state → HTTP 409."""


class ValidationError(DomainError):
    """Business rule violation → HTTP 422."""


class PermissionError(DomainError):
    """Insufficient permissions → HTTP 403."""


class InvalidStateTransitionError(DomainError):
    """Workflow state transition is not allowed → HTTP 422 with code INVALID_TRANSITION."""


class AuthenticationError(DomainError):
    """Invalid credentials → HTTP 401."""
