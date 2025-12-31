"""Domain errors for Test aggregate"""
from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class TestNotFoundError(Error):
    def __init__(self, test_id: str):
        super().__init__(f"Test with ID {test_id} not found", ErrorCode.NOT_FOUND)


class InvalidTestDataError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)


class TestPublishedError(Error):
    def __init__(self, operation: str):
        super().__init__(
            f"Cannot {operation} on published test",
            ErrorCode.CONFLICT
        )


class TestAlreadyArchivedError(Error):
    def __init__(self):
        super().__init__("Test is already archived", ErrorCode.CONFLICT)


class InvalidTestStatusError(Error):
    def __init__(self, current_status: str, required_status: str):
        super().__init__(
            f"Test must be in {required_status} status, but is currently {current_status}",
            ErrorCode.CONFLICT
        )


class PassageCountMismatchError(Error):
    def __init__(self, test_type: str, expected: int, actual: int):
        super().__init__(
            f"{test_type} requires exactly {expected} passage(s), but has {actual}",
            ErrorCode.INVALID_DATA
        )


class MaxPassageCountExceededError(Error):
    def __init__(self, test_type: str, max_count: int):
        super().__init__(
            f"{test_type} can have maximum {max_count} passage(s)",
            ErrorCode.INVALID_DATA
        )


class DuplicatePassageError(Error):
    def __init__(self, passage_id: str):
        super().__init__(
            f"Passage {passage_id} already exists in test",
            ErrorCode.CONFLICT
        )


class NoPassagesError(Error):
    def __init__(self):
        super().__init__("Test must have at least one passage", ErrorCode.INVALID_DATA)
