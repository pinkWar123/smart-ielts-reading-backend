from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.queries.get_paginated_single_tests.get_paginated_single_tests_dto import (
    GetPaginatedSingleTestsQuery,
    GetPaginatedSingleTestsResponse,
)

from .get_paginated_single_tests_dto import TestDTO


class GetPaginatedSingleTestsUseCase(
    UseCase[GetPaginatedSingleTestsQuery, GetPaginatedSingleTestsResponse]
):
    def __init__(self, test_query_service: TestQueryService):
        self.test_query_service = test_query_service

    async def execute(
        self, request: GetPaginatedSingleTestsQuery
    ) -> GetPaginatedSingleTestsResponse:
        test_query_model = await self.test_query_service.get_paginated_single_tests_with_question_types(
            page=request.page,
            page_number=request.page_size,
            question_types=request.question_types,
            status=request.status,
        )

        test_dtos = [
            TestDTO(id=test.id, title=test.title, question_types=test.question_types)
            for test in test_query_model.data
        ]

        return GetPaginatedSingleTestsResponse(
            data=test_dtos, meta=test_query_model.meta
        )
