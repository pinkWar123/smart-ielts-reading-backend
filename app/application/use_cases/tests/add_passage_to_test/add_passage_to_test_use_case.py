from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.create_test.create_test_dtos import (
    AddPassageToTestRequest,
    TestResponse,
)
from app.domain.errors.passage_errors import PassageNotFoundError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.repositories.passage_repository import PassageRepositoryInterface
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.infrastructure.repositories.sql_passage_repository import (
    SQLPassageRepositoryInterface,
)
from app.infrastructure.repositories.sql_test_repository import SQLTestRepository


class AddPassageToTestUseCase(UseCase[AddPassageToTestRequest, TestResponse]):
    """Use case for adding a complete passage to a test"""

    def __init__(
        self,
        test_repository: TestRepositoryInterface,
        passage_repository: PassageRepositoryInterface,
    ):
        self.test_repository = test_repository
        self.passage_repository = passage_repository

    async def execute(
        self, test_id: str, request: AddPassageToTestRequest
    ) -> TestResponse:
        """
        Add a complete passage to a test

        Args:
            test_id: ID of the test to add passage to
            request: AddPassageToTestRequest with passage ID

        Returns:
            TestResponse with updated test data

        Raises:
            ValueError: If test or passage not found, or business rules violated
        """
        # Get the test
        test = await self.test_repository.get_by_id(test_id)
        if not test:
            raise TestNotFoundError(test_id)

        # Get the passage with questions to verify it exists and get its data
        # Use get_by_id_with_questions if the repository is SQL-based
        if isinstance(self.passage_repository, SQLPassageRepositoryInterface):
            passage = await self.passage_repository.get_by_id_with_questions(
                request.passage_id
            )
        else:
            passage = await self.passage_repository.get_by_id(request.passage_id)

        if not passage:
            raise PassageNotFoundError(request.passage_id)

        # Use domain method to add passage (enforces business rules)
        test.add_passage(request.passage_id)

        # Calculate new totals based on passage data
        total_questions = passage.get_total_questions()
        total_points = passage.get_total_points()

        # Update totals in test
        # For multiple passages, we would need to sum all passages
        current_total_questions = test.total_questions + total_questions
        current_total_points = test.total_points + total_points
        test.update_totals(current_total_questions, current_total_points)

        # Persist the updated test
        updated_test = await self.test_repository.update(test)

        # Add passage to test_passages association table
        if isinstance(self.test_repository, SQLTestRepository):
            passage_order = len(test.passage_ids)
            await self.test_repository.add_passage_to_test(
                test_id, request.passage_id, passage_order
            )

        return TestResponse.from_entity(updated_test)
