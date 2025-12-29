from abc import ABC

from app.domain.errors.error_codes import ErrorCode


class Error(Exception, ABC):
    def __init__(self, message: str, code: ErrorCode):
        super().__init__(message)
        self.message = message
        self.code = code
