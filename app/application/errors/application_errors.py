from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class ApplicationError(Error):
    """Base class for application-layer errors (HTTP-level concerns)"""

    pass


class InvalidFileTypeError(ApplicationError):
    """Raised when an uploaded file is not of the expected type"""

    def __init__(self, message: str = "File must be an image"):
        super().__init__(message, ErrorCode.BAD_REQUEST)
