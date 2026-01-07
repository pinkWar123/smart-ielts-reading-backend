from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import RequestType, ResponseType, UseCase
from app.application.use_cases.passages.get_test_with_passages.get_test_with_passages_dto import (
    GetTestWithPassagesQuery,
    GetTestWithPassagesResponse,
)
from app.domain.aggregates.passage import Passage
from app.domain.errors.test_errors import TestNotFoundError

from .get_test_with_passages_dto import PassageResponse


class GetTestWithPassagesUseCase(
    UseCase[GetTestWithPassagesQuery, GetTestWithPassagesResponse]
):
    def __init__(self, test_query_service: TestQueryService):
        self.test_query_service = test_query_service

    async def execute(
        self, request: GetTestWithPassagesQuery
    ) -> GetTestWithPassagesResponse:
        test_model = await self.test_query_service.get_test_by_id_with_passages(
            test_id=request.id, status=None, test_type=None
        )
        print([passage.id for passage in test_model.passages])
        if not test_model:
            raise TestNotFoundError(request.test_id)

        test = test_model.to_domain_entity()
        passages_response = [
            self._convert_to_passage_response(passage)
            for passage in test_model.passages
        ]
        return GetTestWithPassagesResponse(
            id=test.id,
            passages=passages_response,
            passage_count=len(test.passage_ids),
        )

    @staticmethod
    def _convert_to_passage_response(passage: Passage) -> PassageResponse:
        # how to reduce content. If the content is too long, we only get the first 100 words, for example
        # Implement for me
        return PassageResponse(
            id=passage.id,
            title=passage.title,
            reduced_content=passage.get_reduced_content(),
            word_count=passage.word_count,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            created_by=passage.created_by,
            created_at=passage.created_at.isoformat(),
            updated_at=passage.updated_at.isoformat() if passage.updated_at else None,
        )
