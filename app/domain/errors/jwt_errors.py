from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class JwtTokenExpiredError(Error):
    def __init__(self, message: str = "JWT token has expired"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenInvalidError(Error):
    def __init__(self, message: str = "JWT token is invalid"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenMissingError(Error):
    def __init__(self, message: str = "JWT token is missing"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenMalformedError(Error):
    def __init__(self, message: str = "JWT token is malformed"):
        super().__init__(message, ErrorCode.BAD_REQUEST)


class RefreshTokenExpiredError(Error):
    def __init__(self, message: str = "Refresh token has expired"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class RefreshTokenRevokedError(Error):
    def __init__(self, message: str = "Refresh token has been revoked"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class RefreshTokenNotFoundError(Error):
    def __init__(self, message: str = "Refresh token not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)
