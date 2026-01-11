"""Domain errors for Class aggregate"""

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class ClassNotFoundError(Error):
    def __init__(self, class_id: str):
        super().__init__(f"Class with ID {class_id} not found", ErrorCode.NOT_FOUND)


class StudentAlreadyEnrolledError(Error):
    def __init__(self, student_id: str, class_id: str):
        super().__init__(
            f"Student {student_id} is already enrolled in class_ {class_id}",
            ErrorCode.CONFLICT,
        )


class StudentNotInClassError(Error):
    def __init__(self, student_id: str, class_id: str):
        super().__init__(
            f"Student {student_id} is not enrolled in class_ {class_id}",
            ErrorCode.NOT_FOUND,
        )


class ClassAlreadyArchivedError(Error):
    def __init__(self, class_id: str):
        super().__init__(f"Class {class_id} is already archived", ErrorCode.CONFLICT)


class InvalidClassDataError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)
