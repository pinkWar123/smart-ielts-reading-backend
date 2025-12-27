from app.domain.errors.domain_errors import DomainError
from app.domain.errors.error_codes import ErrorCode


class UserNotFoundError(DomainError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)
