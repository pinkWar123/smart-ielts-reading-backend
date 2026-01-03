"""Domain errors for Question entities"""

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class QuestionNotFoundError(Error):
    def __init__(self, question_id: str):
        super().__init__(
            f"Question with ID {question_id} not found", ErrorCode.NOT_FOUND
        )


class QuestionGroupNotFoundError(Error):
    def __init__(self, group_id: str):
        super().__init__(
            f"Question group with ID {group_id} not found", ErrorCode.NOT_FOUND
        )


class InvalidQuestionTypeError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)


class QuestionTypeMismatchError(Error):
    def __init__(self, question_type: str, group_type: str):
        super().__init__(
            f"Question type '{question_type}' does not match group type '{group_type}'",
            ErrorCode.INVALID_DATA,
        )


class QuestionNumberOutOfRangeError(Error):
    def __init__(self, question_number: int, start: int, end: int):
        super().__init__(
            f"Question number {question_number} is not in group range {start}-{end}",
            ErrorCode.INVALID_DATA,
        )


class InvalidQuestionGroupRangeError(Error):
    def __init__(self, start: int, end: int):
        super().__init__(
            f"Invalid question range: end ({end}) must be >= start ({start})",
            ErrorCode.INVALID_DATA,
        )


class DuplicateQuestionGroupOrderError(Error):
    def __init__(self, order: int):
        super().__init__(
            f"Question group with order {order} already exists", ErrorCode.CONFLICT
        )


class MissingOptionsError(Error):
    def __init__(self, question_type: str):
        super().__init__(
            f"{question_type} questions must have options", ErrorCode.INVALID_DATA
        )


class InvalidQuestionOptionsError(Error):
    def __init__(self, question_type: str):
        super().__init__(
            f"{question_type} questions in a group should not have individual options. "
            "Options should be defined at the group level.",
            ErrorCode.INVALID_DATA,
        )
