"""Domain errors for Class aggregate"""

from typing import List

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class ClassNotFoundError(Error):
    def __init__(self, class_id: str):
        super().__init__(f"Class with ID {class_id} not found", ErrorCode.NOT_FOUND)


class ClassNameHasExisted(Error):
    def __init__(self, class_name: str):
        super().__init__(
            f"Class with name {class_name} has already existed", ErrorCode.CONFLICT
        )


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


class NoPermissionToCreateClassError(Error):
    def __init__(self, user_id: str):
        super().__init__(
            f"User {user_id} does not have permission to create a class",
            ErrorCode.FORBIDDEN,
        )


class NoPermissionToAddStudentError(Error):
    def __init__(self, user_id: str):
        super().__init__(
            f"User {user_id} does not have permission to add a student to a class",
            ErrorCode.FORBIDDEN,
        )


class NoPermissionToRemoveStudentError(Error):
    def __init__(self, user_id: str):
        super().__init__(
            f"User {user_id} does not have permission to remove a student from a class",
            ErrorCode.FORBIDDEN,
        )


class NotATeacherError(Error):
    def __init__(self, user_id: str):
        super().__init__(
            f"User {user_id} is neither a teacher nor an admin", ErrorCode.FORBIDDEN
        )


class NoTeachersError(Error):
    def __init__(self, teacher_ids: List[str]):
        super().__init__(
            f"None of users with ids {teacher_ids} are teachers", ErrorCode.BAD_REQUEST
        )


class NoStudentsError(Error):
    def __init__(self, student_ids: List[str]):
        super().__init__(
            f"None of users with ids {student_ids} are students", ErrorCode.BAD_REQUEST
        )


class NotAStudent(Error):
    def __init__(self, user_id: str):
        super().__init__(f"User {user_id} is not a student", ErrorCode.FORBIDDEN)


class ClassAlreadyArchivedError(Error):
    def __init__(self, class_id: str):
        super().__init__(f"Class {class_id} is already archived", ErrorCode.CONFLICT)


class InvalidClassDataError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)


class TeacherAlreadyAssignedError(Error):
    def __init__(self, teacher_id: str, class_id: str):
        super().__init__(
            f"Teacher {teacher_id} is already assigned to class {class_id}",
            ErrorCode.CONFLICT,
        )


class TeacherNotInClassError(Error):
    def __init__(self, teacher_id: str, class_id: str):
        super().__init__(
            f"Teacher {teacher_id} is not assigned to class {class_id}",
            ErrorCode.NOT_FOUND,
        )


class CannotRemoveLastTeacherError(Error):
    def __init__(self, class_id: str):
        super().__init__(
            f"Cannot remove the last teacher from class {class_id}. At least one teacher is required",
            ErrorCode.INVALID_DATA,
        )
