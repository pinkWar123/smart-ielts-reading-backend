from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.passages.commands.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)
from app.domain.errors.passage_errors import InvalidPassageDataError
from app.domain.repositories.passage_repository import PassageRepositoryInterface


class CreatePassageUseCase(UseCase[CreatePassageRequest, PassageResponse]):
    def __init__(self, passage_repo: PassageRepositoryInterface):
        self.passage_repo = passage_repo

    async def execute(self, request: CreatePassageRequest) -> PassageResponse:
        if not request.title or len(request.title.strip()) == 0:
            raise InvalidPassageDataError("Title cannot be empty")

        if not request.content or len(request.content.strip()) == 0:
            raise InvalidPassageDataError("Content cannot be empty")

        passage_entity = await self.passage_repo.create(
            title=request.title.strip(),
            content=request.content.strip(),
            author_id=request.author_id,
        )

        return PassageResponse.from_entity(passage_entity)
