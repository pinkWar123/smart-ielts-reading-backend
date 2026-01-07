from app.application.use_cases.base.use_case import QueryUseCase
from app.application.use_cases.passages.create_passage.create_passage_dtos import (
    PassageResponse,
)
from app.domain.repositories.passage_repository import PassageRepositoryInterface


class GetPassagesUseCase(QueryUseCase[list[PassageResponse]]):
    def __init__(self, passage_repo: PassageRepositoryInterface):
        self.passage_repo = passage_repo

    async def execute(self) -> list[PassageResponse]:
        passages = await self.passage_repo.get_all()
        return [PassageResponse.from_entity(passage) for passage in passages]
