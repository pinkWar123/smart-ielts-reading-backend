from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class UserNotFoundError(Error):
    def __init__(self, message: str = "User not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)


class StudentNotFoundError(Error):
    def __init__(self, message: str = "Student not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)


class UsernameAlreadyExistsError(Error):
    def __init__(self, message: str = "User already exists"):
        super().__init__(message, ErrorCode.CONFLICT)


class EmailAlreadyBeenUsedError(Error):
    def __init__(self, message: str = "Email has already been used"):
        super().__init__(message, ErrorCode.CONFLICT)


class WrongPasswordError(Error):
    def __init__(self, message: str = "Wrong password"):
        super().__init__(message, ErrorCode.BAD_REQUEST)
