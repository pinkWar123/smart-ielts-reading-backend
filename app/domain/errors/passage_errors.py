from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class PassageNotFoundError(Error):
    def __init__(self, passage_id: str):
        super().__init__(f"Passage with ID {passage_id} not found", ErrorCode.NOT_FOUND)


class InvalidPassageDataError(Error):
    def __init__(self, message: str = "Invalid passage data"):
        super().__init__(message, ErrorCode.INVALID_DATA)


class NoQuestionsError(Error):
    def __init__(self):
        super().__init__(
            "Passage must have at least one question", ErrorCode.INVALID_DATA
        )


class InvalidQuestionReferenceError(Error):
    def __init__(self, question_id: str, group_id: str):
        super().__init__(
            f"Question {question_id} references non-existent group {group_id}",
            ErrorCode.INVALID_DATA,
        )
