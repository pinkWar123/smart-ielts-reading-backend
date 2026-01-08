from app.application.services.query.passages.passages_query_model import AuthorInfo
from app.application.services.query.passages.passages_query_service import (
    PassagesQueryService,
)
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.common.dtos.passage_detail_dto import (
    QuestionGroupDTO,
    UserView,
)
from app.application.use_cases.passages.queries.get_passage_detail_by_id.get_passage_detail_dto import (
    GetPassageDetailByIdQuery,
    GetPassageDetailByIdResponse,
)
from app.domain.errors.passage_errors import PassageNotFoundError


class GetPassageDetailByIdUseCase(
    UseCase[GetPassageDetailByIdQuery, GetPassageDetailByIdResponse]
):
    def __init__(self, passage_query_service: PassagesQueryService):
        self.passage_query_service = passage_query_service

    async def execute(
        self, request: GetPassageDetailByIdQuery
    ) -> GetPassageDetailByIdResponse:
        passage_detail = await self.passage_query_service.get_passage_detail_by_id(
            request.id
        )
        if not passage_detail:
            raise PassageNotFoundError(request.id)

        response = GetPassageDetailByIdResponse(
            title=passage_detail.title,
            content=passage_detail.content,
            difficulty_level=passage_detail.difficulty_level,
            topic=passage_detail.topic,
            source=passage_detail.source,
            question_groups=(
                [
                    QuestionGroupDTO.convert_to_dto(qg, UserView.ADMIN)
                    for qg in passage_detail.question_groups
                ]
                if passage_detail.question_groups
                else []
            ),
            created_by=AuthorInfo(
                id=passage_detail.id,
                username=passage_detail.created_by.username,
                full_name=passage_detail.created_by.full_name,
                email=passage_detail.created_by.email,
            ),
        )

        return response
