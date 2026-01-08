from typing import BinaryIO, Optional

from app.application.errors.ocr_errors import InvalidContent, InvalidFile
from app.application.services.image_to_text_service import IImageToTextService


class ExtractTextFromImageUseCase:
    def __init__(self, image_to_text_service: IImageToTextService):
        self.image_to_text_service = image_to_text_service

    async def execute(
        self, image_data: bytes, prompt: Optional[str] = None, content_type: str = None
    ) -> str:
        """Extract text from an image using OCR service.

        Args:
            image_data: The image file content as bytes
            prompt: Optional prompt for the OCR service
            content_type: MIME type of the uploaded file

        Raises:
            InvalidFile: If the file is not an image
            InvalidContent: If the extracted content is invalid
        """
        # Validate file type
        if content_type and not content_type.startswith("image/"):
            raise InvalidFile("File must be an image")

        response = await self.image_to_text_service.extract_text_from_image(image_data)
        if response == "NO":
            raise InvalidContent()

        return response
