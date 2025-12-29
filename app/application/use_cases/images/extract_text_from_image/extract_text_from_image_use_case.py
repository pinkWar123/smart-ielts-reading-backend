from typing import BinaryIO

from app.application.errors.ocr_errors import InvalidContent
from app.application.services.image_to_text_service import IImageToTextService


class ExtractTextFromImageUseCase:
    def __init__(self, image_to_text_service: IImageToTextService):
        self.image_to_text_service = image_to_text_service

    async def execute(self, image_data: bytes, prompt: str = None) -> str:
        """Extract text from an image using OCR service."""
        response = await self.image_to_text_service.extract_text_from_image(image_data)
        if response == "NO":
            raise InvalidContent()

        return response
