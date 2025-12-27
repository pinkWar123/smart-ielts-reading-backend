from app.domain.errors.domain_errors import DomainError
from app.domain.errors.error_codes import ErrorCode


class JwtTokenExpiredError(DomainError):
    def __init__(self, message: str = "JWT token has expired"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenInvalidError(DomainError):
    def __init__(self, message: str = "JWT token is invalid"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenMissingError(DomainError):
    def __init__(self, message: str = "JWT token is missing"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class JwtTokenMalformedError(DomainError):
    def __init__(self, message: str = "JWT token is malformed"):
        super().__init__(message, ErrorCode.BAD_REQUEST)


class RefreshTokenExpiredError(DomainError):
    def __init__(self, message: str = "Refresh token has expired"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class RefreshTokenRevokedError(DomainError):
    def __init__(self, message: str = "Refresh token has been revoked"):
        super().__init__(message, ErrorCode.UNAUTHORIZED)


class RefreshTokenNotFoundError(DomainError):
    def __init__(self, message: str = "Refresh token not found"):
        super().__init__(message, ErrorCode.NOT_FOUND)
