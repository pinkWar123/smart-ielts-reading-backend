from app.application.services.query.tests.test_query_model import (
    TestWithPassagesQueryModel,
)
from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import RequestType, ResponseType, UseCase
from app.application.use_cases.passages.delete_passage_by_id.delete_passage_by_id_dto import (
    DeletePassageByIdRequest,
    DeletePassageByIdResponse,
)
from app.domain.aggregates.test import Test
from app.domain.errors.test_errors import PassageNotInTestError, TestNotFoundError
from app.domain.repositories.test_repository import TestRepositoryInterface


class DeletePassageByIdUseCase(
    UseCase[DeletePassageByIdRequest, DeletePassageByIdResponse]
):
    def __init__(
        self,
        test_query_service: TestQueryService,
        test_repository: TestRepositoryInterface,
    ):
        self.test_query_service = test_query_service
        self.test_repository = test_repository

    async def execute(
        self, request: DeletePassageByIdRequest
    ) -> DeletePassageByIdResponse:
        test_query_model = await self.test_query_service.get_test_by_id_with_passages(
            test_id=request.test_id, status=None, test_type=None
        )
        if test_query_model is None:
            raise TestNotFoundError(request.test_id)

        test = self._convert_to_domain_entity(test_query_model)
        test.remove_passage(request.passage_id)

        # Persist the changes to the database
        await self.test_repository.update(test)

        response = DeletePassageByIdResponse(
            passage_id=request.passage_id,
            passage_count=len(test.passage_ids),
            deleted=True,
        )

        return response

    @staticmethod
    def _convert_to_domain_entity(test: TestWithPassagesQueryModel) -> Test:
        return Test(
            id=test.id,
            title=test.title,
            description=test.description,
            test_type=test.test_type,
            passage_ids=test.passage_ids,
            time_limit_minutes=test.time_limit_minutes,
            total_questions=test.total_questions,
            total_points=test.total_points,
            status=test.status,
            created_by=test.created_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            is_active=test.is_active,
        )
