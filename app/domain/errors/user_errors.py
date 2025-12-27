from app.domain.errors.domain_errors import DomainError
from app.domain.errors.error_codes import ErrorCode


class UserNotFoundError(DomainError):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)


class UsernameAlreadyExistsError(DomainError):
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, ErrorCode.CONFLICT)


class EmailAlreadyBeenUsedError(DomainError):
    def __init__(self, message: str = "Email has already been used"):
        super().__init__(message, ErrorCode.CONFLICT)


class WrongPasswordError(DomainError):
    def __init__(self, message: str = "Wrong password"):
        super().__init__(message, ErrorCode.BAD_REQUEST)
