from app.application.services.passage_service import PassageService
from app.application.use_cases.passages.create_passage.create_passage_dtos import (
    PassageResponse,
)


class GetAllPassagesUseCase:
    """Use case for retrieving all passages"""

    def __init__(self, passage_service: PassageService):
        self.passage_service = passage_service

    async def execute(self) -> list[PassageResponse]:
        """Execute the use case to get all passages"""
        return await self.passage_service.get_all_passages()
