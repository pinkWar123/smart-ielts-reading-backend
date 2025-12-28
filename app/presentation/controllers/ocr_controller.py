# app/presentation/controllers/ocr_controller.py
from typing import Optional

from fastapi import File, Form, UploadFile

from app.use_cases.images.extract_text_from_image.extract_text_from_image_use_case import (
    ExtractTextFromImageUseCase,
)


class OcrController:
    def __init__(self, extract_text_use_case: ExtractTextFromImageUseCase):
        self._extract_text_use_case = extract_text_use_case

    async def extract_text_from_image(
        self, file: UploadFile = File(...), prompt: Optional[str] = Form(None)
    ) -> dict:
        """Extract text from an uploaded image."""
        if not file.content_type.startswith("image/"):
            raise ValueError("File must be an image")

        file_content = await file.read()

        text = await self._extract_text_use_case.execute(file_content, prompt)

        return {
            "filename": file.filename,
            "extracted_text": text,
            "prompt_used": prompt,
        }
