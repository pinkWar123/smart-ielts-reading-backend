from abc import ABC, abstractmethod

from app.domain.entities.test import Test


class IContentToTestService(ABC):
    @abstractmethod
    async def extract_test_from_image(self, image_data: bytes) -> Test:
        """Extract structured test data from an image"""
        pass

    @abstractmethod
    async def extract_test_from_text(self, text_content: str) -> Test:
        """Parse text content into structured test data"""
        pass

    @abstractmethod
    async def validate_extracted_content(self, test: Test) -> bool:
        """Validate extracted test content against domain rules."""
        pass
