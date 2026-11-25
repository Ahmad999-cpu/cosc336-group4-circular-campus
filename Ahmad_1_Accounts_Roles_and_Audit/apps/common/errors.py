"""Domain errors. The codes match the error statuses in Table 9.1 of the design document."""


class DomainError(Exception):
    """A business rule refused the operation. `code` is shown to the caller and written to the audit log."""

    code = "DOMAIN_ERROR"

    def __init__(self, message: str = "", code: str | None = None):
        super().__init__(message or self.code)
        if code:
            self.code = code


class InvalidTransition(DomainError):
    code = "INVALID_TRANSITION"


class Forbidden(DomainError):
    code = "FORBIDDEN"


class SelfApproval(DomainError):
    code = "SELF_APPROVAL"


class InsufficientQuantity(DomainError):
    code = "INSUFFICIENT_QUANTITY"


class Conflict(DomainError):
    """Someone else changed the record first (optimistic lock on rowVersion)."""

    code = "CONFLICT"


class ValidationFailed(DomainError):
    code = "VALIDATION_ERROR"
