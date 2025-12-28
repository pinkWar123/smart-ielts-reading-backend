from abc import ABC, abstractmethod
from typing import Optional


class IImageToTextService(ABC):
    @abstractmethod
    async def extract_text_from_image(self, image_data: bytes) -> str:
        """Extract text content from the image using OCR/Vision API."""
        pass

    @abstractmethod
    async def validate_image(self, image_data: bytes) -> bool:
        """Validate an image format, size, and readability."""
        pass

    @abstractmethod
    async def preprocess_image(self, image_data: bytes) -> bytes:
        """Preprocess image for better text extraction (resize, enhance)."""
        pass

    @abstractmethod
    async def get_confidence_score(self, image_data: bytes) -> Optional[float]:
        """Get a confidence score of text extraction (if supported)."""
        pass
