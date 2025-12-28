from abc import ABC, abstractmethod
from typing import Tuple


class IImageProcessorService(ABC):
    @abstractmethod
    async def validate_image(self, image_data: bytes) -> bool:
        """Validate image format and size constraints."""
        pass

    @abstractmethod
    async def process_for_api(self, image_data: bytes) -> Tuple[bytes, str]:
        """Process image for Claude API (resize, compress, encode)."""
        pass

    @abstractmethod
    async def get_supported_formats(self) -> list[str]:
        """Return list of supported image formats."""
        pass
