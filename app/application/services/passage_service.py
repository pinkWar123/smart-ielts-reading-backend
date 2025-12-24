from app.domain.entities.passage import Passage
from app.domain.repositories.passage_repository import PassageRepository
from app.use_cases.passages.create_passage.create_passage_dtos import PassageResponse


class PassageService:
    def __init__(self, passage_repo: PassageRepository):
        self.passage_repo = passage_repo

    async def get_all_passages(self) -> list[PassageResponse]:
        passages = await self.passage_repo.get_all()
        return [PassageResponse.from_entity(passage) for passage in passages]
