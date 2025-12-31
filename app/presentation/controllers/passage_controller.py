from fastapi import HTTPException, status

from app.application.services.passage_service import PassageService
from app.application.use_cases.passages.create_complete_passage.create_complete_passage_dtos import (
    CompletePassageResponse,
    CreateCompletePassageRequest,
)
from app.application.use_cases.passages.create_complete_passage.create_complete_passage_use_case import (
    CreateCompletePassageUseCase,
)
from app.application.use_cases.passages.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)
from app.domain.errors.domain_errors import Error
from app.domain.errors.error_codes import ErrorCode
from app.domain.errors.passage_errors import InvalidPassageDataError


class PassageController:
    def __init__(
        self,
        passage_service: PassageService,
        create_complete_passage_use_case: CreateCompletePassageUseCase,
    ):
        self.passage_service = passage_service
        self.create_complete_passage_use_case = create_complete_passage_use_case

    async def create_passage(self, request: CreatePassageRequest) -> PassageResponse:
        try:
            # TODO: Implement create passage through service
            raise NotImplementedError("Create passage not yet implemented")
        except InvalidPassageDataError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def create_complete_passage(
        self, request: CreateCompletePassageRequest, user_id: str
    ) -> CompletePassageResponse:
        """
        Create a complete passage with questions and question groups

        Args:
            request: CreateCompletePassageRequest with passage data
            user_id: ID of the admin creating the passage

        Returns:
            CompletePassageResponse with created passage

        Raises:
            HTTPException: If creation fails or validation errors occur
        """
        try:
            return await self.create_complete_passage_use_case.execute(request, user_id)
        except Error as e:
            raise HTTPException(
                status_code=self._map_error_code_to_status(e.code),
                detail=e.message,
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create passage: {str(e)}",
            )

    async def get_all_passages(self) -> list[PassageResponse]:
        return await self.passage_service.get_all_passages()

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
