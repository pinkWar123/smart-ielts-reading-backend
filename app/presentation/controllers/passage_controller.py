from fastapi import HTTPException

from app.application.services.passage_service import PassageService
from app.domain.errors.passage_errors import InvalidPassageDataError
from app.application.use_cases.passages.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)


class PassageController:
    def __init__(self, passage_service: PassageService):
        self.passage_service = passage_service

    async def create_passage(self, request: CreatePassageRequest) -> PassageResponse:
        try:
            # TODO: Implement create passage through service
            raise NotImplementedError("Create passage not yet implemented")
        except InvalidPassageDataError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_all_passages(self) -> list[PassageResponse]:
        return await self.passage_service.get_all_passages()
