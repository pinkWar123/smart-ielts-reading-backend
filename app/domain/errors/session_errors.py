"""Domain errors for Session aggregate"""

from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class SessionNotFoundError(Error):
    def __init__(self, session_id: str):
        super().__init__(f"Session with ID {session_id} not found", ErrorCode.NOT_FOUND)


class InvalidSessionStatusError(Error):
    def __init__(self, session_id: str, current_status, required_status):
        super().__init__(
            f"Session {session_id} must be in {required_status} status, but is currently {current_status}",
            ErrorCode.CONFLICT,
        )


class SessionNotJoinableError(Error):
    def __init__(self, session_id: str, current_status):
        super().__init__(
            f"Cannot join session {session_id} in {current_status} status. Session must be in WAITING_FOR_STUDENTS or IN_PROGRESS status.",
            ErrorCode.CONFLICT,
        )


class NoStudentsConnectedError(Error):
    def __init__(self, session_id: str):
        super().__init__(
            f"Cannot start session {session_id}: no students are connected",
            ErrorCode.CONFLICT,
        )


class CannotCancelActiveSessionError(Error):
    def __init__(self, session_id: str):
        super().__init__(
            f"Cannot cancel session {session_id}: session is currently IN_PROGRESS",
            ErrorCode.CONFLICT,
        )


class StudentNotInSessionError(Error):
    def __init__(self, student_id: str, session_id: str):
        super().__init__(
            f"Student {student_id} is not a participant in session {session_id}",
            ErrorCode.NOT_FOUND,
        )


class InvalidSessionDataError(Error):
    def __init__(self, message: str):
        super().__init__(message, ErrorCode.INVALID_DATA)
