from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class InvalidContent(Error):
    def __init__(
        self,
        message: str = "Extracted content is invalid, it must be a reading passage",
    ):
        super().__init__(message, ErrorCode.BAD_REQUEST)


class InvalidFile(Error):
    def __init__(self, message: str = "File type is invalid"):
        super().__init__(message, ErrorCode.BAD_REQUEST)
