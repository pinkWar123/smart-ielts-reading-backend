from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import RequestType, ResponseType, UseCase
from app.application.use_cases.tests.queries.get_paginated_full_tests.get_paginated_full_tests_dto import (
    FullTestDTO,
    GetPaginatedFullTestsQuery,
    GetPaginatedFullTestsResponse,
)


class GetPaginatedFullTestsUseCase(
    UseCase[GetPaginatedFullTestsQuery, GetPaginatedFullTestsResponse]
):
    def __init__(self, test_query_service: TestQueryService):
        self.test_query_service = test_query_service

    async def execute(
        self, request: GetPaginatedFullTestsQuery
    ) -> GetPaginatedFullTestsResponse:
        tests = await self.test_query_service.get_paginated_full_tests(
            page=request.page, page_number=request.page_size
        )

        test_dtos = [FullTestDTO(id=test.id, title=test.title) for test in tests.data]
        return GetPaginatedFullTestsResponse(data=test_dtos, meta=tests.meta)
