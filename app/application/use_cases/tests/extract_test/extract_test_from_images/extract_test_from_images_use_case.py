import asyncio
import base64
import io
from typing import Any

from PIL import Image

from app.application.services.test_generator_service import ITestGeneratorService
from app.application.use_cases.base.use_case import RequestType, ResponseType, UseCase
from app.application.use_cases.tests.extract_test.extract_test_from_images.constants import (
    MAX_IMAGES_NUMBER,
)
from app.application.use_cases.tests.extract_test.extract_test_from_images.errors import (
    ExceedingMaxImagesError,
    NoImagesError,
)
from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_dto import (
    ExtractedTestResponse,
    ImagesExtractRequest,
)
from app.application.use_cases.tests.extract_test.extract_test_from_images.prompt import (
    EXTRACTION_PROMPT,
)


class ExtractTestFromImagesUseCase(
    UseCase[ImagesExtractRequest, ExtractedTestResponse]
):
    def __init__(self, test_generator_service: ITestGeneratorService):
        self.test_generator_service = test_generator_service

    async def execute(self, request: ImagesExtractRequest) -> ExtractedTestResponse:
        images = request.images
        if not images:
            raise NoImagesError()

        if len(images) > MAX_IMAGES_NUMBER:
            raise ExceedingMaxImagesError()

        processed_images = await asyncio.gather(
            *[self._preprocess_image(self, img) for img in images]
        )

        prompt = await self.build_prompt(self, processed_images, request)
        response = await self.test_generator_service.generate_test(prompt)

        return response

    @staticmethod
    async def build_prompt(
        self, processed_images: list[Any], request: ImagesExtractRequest
    ) -> str:
        content = []
        for i, img_data in enumerate(processed_images):
            base64_image = base64.b64encode(img_data).decode("utf-8")
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64_image,
                    },
                }
            )

            content.append(
                {"type": "text", "text": f"[Image {i + 1} of {len(request.images)}]"}
            )

        prompt = EXTRACTION_PROMPT
        if request.test_title:
            prompt += f"\n\nTest Title: {request.test_title}"
        if request.extraction_hints:
            prompt += f"\n\nAdditional Hints: {request.extraction_hints}"

        content.append({"type": "text", "text": prompt})

        return content

    @staticmethod
    async def _preprocess_image(self, image_data: bytes) -> bytes:
        """Preprocess image for better Claude Vision analysis."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Resize if too large while maintaining aspect ratio
                max_size = (2048, 2048)
                if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                    img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save as JPEG with good quality
                output = io.BytesIO()
                img.save(output, format="JPEG", quality=85, optimize=True)
                return output.getvalue()

        except Exception:
            # If preprocessing fails, return original
            return image_data
