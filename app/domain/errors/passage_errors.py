from app.domain.errors.domain_errors import DomainError


class PassageNotFoundError(DomainError):
    def __init__(self):
        super().__init__("Passage not found", "NOT_FOUND")


class InvalidPassageDataError(DomainError):
    def __init__(self, message: str = "Invalid passage data"):
        super().__init__(message, "INVALID_DATA")
