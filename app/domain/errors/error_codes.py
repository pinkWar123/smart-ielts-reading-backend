from enum import Enum


class ErrorCode(Enum):
    NOT_FOUND = "NOT_FOUND"
    INVALID_DATA = "INVALID_DATA"
    UNAUTHORIZED = "UNAUTHORIZED"
    CONFLICT = "CONFLICT"
    BAD_REQUEST = "BAD_REQUEST"
    INTERNAL_ERROR = "INTERNAL_ERROR"

    def __init__(self, code: str):
        self.code = code

    def __str__(self):
        return self.code
