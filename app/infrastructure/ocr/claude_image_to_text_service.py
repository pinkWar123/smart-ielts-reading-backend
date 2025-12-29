# app/application/services/claude_image_to_text_service.py
import asyncio
import base64
import io
from typing import Optional

from anthropic import AsyncAnthropic
from PIL import Image

from app.application.services.image_to_text_service import IImageToTextService
from app.common.settings import Settings

MAX_IMAGE_SIZE_BYTES = 20 * 1024 * 1024


class ClaudeImageToTextService(IImageToTextService):
    def __init__(self, settings: Settings, client: AsyncAnthropic):
        self.client = client
        self.model = settings.claude_model
        self.max_retries = settings.max_retry_attempts

    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text from image using Claude Vision API with retry logic."""
        processed_image = await self.preprocess_image(image_data)
        base64_image = base64.b64encode(processed_image).decode("utf-8")

        prompt = """Please extract all text content from this image. 
        Return only the text content without any additional commentary or formatting.
        Maintain the original structure and line breaks where appropriate."""

        for attempt in range(self.max_retries):
            try:
                response = await self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": base64_image,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                )

                return response.content[0].text.strip()

            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(
                        f"Failed to extract text after {self.max_retries} attempts: {str(e)}"
                    )

                # Exponential backoff
                await asyncio.sleep(2**attempt)

    async def validate_image_format(self, image_data: bytes) -> bool:
        """Validate image format and size constraints."""
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Check format
                if img.format not in ["JPEG", "PNG", "WEBP"]:
                    return False

                # Check size constraints (Claude API limits)
                if len(image_data) > MAX_IMAGE_SIZE_BYTES:  # 20MB limit
                    return False

                # Check dimensions
                width, height = img.size
                if width < 50 or height < 50:  # Too small
                    return False

                return True
        except Exception:
            return False

    async def preprocess_image(self, image_data: bytes) -> bytes:
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

    async def get_confidence_score(self, image_data: bytes) -> Optional[float]:
        """Claude doesn't provide confidence scores, return None."""
        return None
