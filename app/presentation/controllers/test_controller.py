from fastapi import HTTPException, status

from app.application.use_cases.tests.add_passage_to_test.add_passage_to_test_use_case import (
    AddPassageToTestUseCase,
)
from app.application.use_cases.tests.create_test.create_test_dtos import (
    AddPassageToTestRequest,
    CreateTestRequest,
    TestResponse,
)
from app.application.use_cases.tests.create_test.create_test_use_case import (
    CreateTestUseCase,
)
from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode


class TestController:
    """Controller for test-related endpoints"""

    def __init__(
        self,
        create_test_use_case: CreateTestUseCase,
        add_passage_to_test_use_case: AddPassageToTestUseCase,
    ):
        self.create_test_use_case = create_test_use_case
        self.add_passage_to_test_use_case = add_passage_to_test_use_case

    async def create_test(
        self, request: CreateTestRequest, user_id: str
    ) -> TestResponse:
        """
        Create a new empty test

        Args:
            request: CreateTestRequest with test details
            user_id: ID of the admin creating the test

        Returns:
            TestResponse with created test data

        Raises:
            HTTPException: If creation fails
        """
        try:
            return await self.create_test_use_case.execute(request, user_id)
        except Error as e:
            raise HTTPException(
                status_code=self._map_error_code_to_status(e.code),
                detail=e.message,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create test: {str(e)}",
            )

    async def add_passage_to_test(
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
            HTTPException: If addition fails or business rules are violated
        """
        try:
            return await self.add_passage_to_test_use_case.execute(test_id, request)
        except Error as e:
            raise HTTPException(
                status_code=self._map_error_code_to_status(e.code),
                detail=e.message,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add passage to test: {str(e)}",
            )

    @staticmethod
    def _map_error_code_to_status(error_code: ErrorCode) -> int:
        """Map domain error codes to HTTP status codes"""
        mapping = {
            ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
            ErrorCode.INVALID_DATA: status.HTTP_400_BAD_REQUEST,
            ErrorCode.CONFLICT: status.HTTP_409_CONFLICT,
            ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
            ErrorCode.BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
        }
        return mapping.get(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
