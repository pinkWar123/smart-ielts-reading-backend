from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.create_test.create_test_dtos import (
    CreateTestRequest,
    TestResponse,
)
from app.domain.entities.test import Test, TestStatus
from app.domain.repositories.test_repository import TestRepositoryInterface


class CreateTestUseCase(UseCase[CreateTestRequest, TestResponse]):
    """Use case for creating an empty test"""

    def __init__(self, test_repository: TestRepositoryInterface):
        self.test_repository = test_repository

    async def execute(self, request: CreateTestRequest, user_id: str) -> TestResponse:
        """
        Create a new empty test

        Args:
            request: CreateTestRequest with test details
            user_id: ID of the admin user creating the test

        Returns:
            TestResponse with created test data
        """
        # Create test domain entity with minimal info
        # Set totals to 0 initially as no passages are added yet
        test = Test(
            title=request.title,
            description=request.description,
            test_type=request.test_type,
            time_limit_minutes=request.time_limit_minutes,
            total_questions=0,  # Will be updated when passages are added
            total_points=0,  # Will be updated when passages are added
            status=TestStatus.DRAFT,
            created_by=user_id,
        )

        # Persist the test
        created_test = await self.test_repository.create(test)

        return TestResponse.from_entity(created_test)
