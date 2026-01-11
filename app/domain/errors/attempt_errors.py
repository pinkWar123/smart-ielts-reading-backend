"""Domain errors for Attempt aggregate"""

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class AttemptNotFoundError(Error):
    def __init__(self, attempt_id: str):
        super().__init__(f"Attempt with ID {attempt_id} not found", ErrorCode.NOT_FOUND)


class InvalidAttemptStatusError(Error):
    def __init__(self, attempt_id: str, current_status):
        super().__init__(
            f"Attempt {attempt_id} is in {current_status} status and cannot be modified",
            ErrorCode.CONFLICT,
        )


class AttemptAlreadySubmittedError(Error):
    def __init__(self, attempt_id: str):
        super().__init__(
            f"Attempt {attempt_id} has already been submitted", ErrorCode.CONFLICT
        )


class InvalidAttemptDataError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)
