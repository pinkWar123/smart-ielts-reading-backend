"""Get All Tests Use Case

This use case retrieves all tests with author information.
Uses TestQueryService for efficient reads with JOINs.
"""

from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.get_all_tests.get_all_tests_dto import (
    Author,
    GetAllTestsQueryParams,
    GetAllTestsResponse,
    TestResponse,
)


class GetAllTestsUseCase(UseCase[GetAllTestsQueryParams, GetAllTestsResponse]):
    """
    Use case for retrieving all tests with author information.

    Uses query service instead of repository for optimized reads.
    This follows CQRS-lite pattern: repositories for writes, query services for reads.
    """

    def __init__(self, test_query_service: TestQueryService):
        self.test_query_service = test_query_service

    async def execute(self, request: GetAllTestsQueryParams) -> GetAllTestsResponse:
        """
        Execute the use case to get all tests with filters.

        Args:
            request: Query parameters containing optional status and type filters

        Returns:
            Response containing list of tests with author information
        """
        # Use query service to fetch tests with authors in a single query
        tests_with_authors = await self.test_query_service.get_all_with_authors(
            status=request.status, test_type=request.type
        )

        # Map query models to response DTOs
        test_responses = [
            TestResponse(
                test_id=test.id,
                title=test.title,
                passage_count=len(test.passage_ids),
                status=test.status,
                type=test.test_type,
                time_limit_minutes=test.time_limit_minutes,
                total_points=test.total_points,
                total_questions=test.total_questions,
                created_by=Author(
                    id=test.author.id,
                    username=test.author.username,
                    email=test.author.email,
                    full_name=test.author.full_name,
                ),
            )
            for test in tests_with_authors
        ]

        return GetAllTestsResponse(tests=test_responses)
