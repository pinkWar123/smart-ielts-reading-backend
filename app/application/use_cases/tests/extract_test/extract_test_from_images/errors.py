from app.application.use_cases.tests.extract_test.extract_test_from_images.constants import (
    MAX_IMAGES_NUMBER,
)
from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class NoImagesError(Error):
    def __init__(self, message: str = "At least one image is required"):
        super().__init__(message, ErrorCode.BAD_REQUEST)


class ExceedingMaxImagesError(Error):
    def __init__(
        self, message: str = f"You can upload a maximum of {MAX_IMAGES_NUMBER} images"
    ):
        super().__init__(message, ErrorCode.BAD_REQUEST)
