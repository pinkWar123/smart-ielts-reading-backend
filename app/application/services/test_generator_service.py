from abc import ABC, abstractmethod

from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_dto import \
    ExtractedTestResponse


class ITestGeneratorService(ABC):
    @abstractmethod
    async def generate_test(self, prompt: str) -> ExtractedTestResponse:
        pass