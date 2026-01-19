from typing import Optional

from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.services.websocket_broadcaster_service import (
    WebSocketBroadcasterService,
)
from app.application.use_cases.attempts.commands.progress.update_progress.update_progress_dto import (
    UpdateProgressRequest,
    UpdateProgressResponse,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.web_socket.message_types import StudentProgressMessage


class UpdateProgressUseCase(
    AuthenticatedUseCase[UpdateProgressRequest, UpdateProgressResponse]
):
    """
    Use case for updating student's progress in an attempt.

    Business rules:
    - Only users can update their own attempt progress
    - Attempt must be IN_PROGRESS status
    - Progress is immediately persisted to database for reconnection support
    - Client should debounce progress updates (e.g., max 1 update per 2 seconds)
    """

    def __init__(
        self,
        attempt_repo: AttemptRepositoryInterface,
        test_query_service: TestQueryService,
        user_repo: UserRepositoryInterface,
        broadcaster: Optional[WebSocketBroadcasterService] = None,
    ):
        self.attempt_repo = attempt_repo
        self.test_query_service = test_query_service
        self.user_repo = user_repo
        self.broadcaster = broadcaster

    async def execute(
        self, request: UpdateProgressRequest, user_id: str
    ) -> UpdateProgressResponse:
        attempt = await self._validate_and_get_attempt(request.attempt_id, user_id)

        # Update progress in domain model
        attempt.update_progress(request.passage_index, request.question_index)

        # Persist to database
        updated_attempt = await self.attempt_repo.update(attempt)

        # Broadcast to teachers if part of a session
        if updated_attempt.session_id and self.broadcaster:
            await self._broadcast_progress_activity(
                attempt=updated_attempt,
                passage_index=request.passage_index,
                question_index=request.question_index,
            )

        return UpdateProgressResponse(
            passage_index=request.passage_index,
            question_index=request.question_index,
            updated_at=TimeHelper.utc_now(),
        )

    async def _validate_and_get_attempt(self, attempt_id: str, user_id: str) -> Attempt:
        """Validate attempt exists, belongs to user, and is in progress."""
        attempt = await self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise AttemptNotFoundError(attempt_id)

        if attempt.student_id != user_id:
            raise NoPermissionToUpdateAttemptError(user_id)

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStatusError(
                attempt_id=attempt_id, current_status=attempt.status
            )

        return attempt

    async def _broadcast_progress_activity(
        self, attempt: Attempt, passage_index: int, question_index: int
    ) -> None:
        """Broadcast student progress activity to teachers."""
        try:
            # Get student name
            student = await self.user_repo.get_by_id(attempt.student_id)
            student_name = student.full_name if student else "Unknown Student"

            # Get test with passages to calculate question number
            test = await self.test_query_service.get_test_by_id_with_passages(
                attempt.test_id
            )

            # Calculate question number based on passage_index and question_index
            question_number = 0
            if test:
                for p_idx, passage in enumerate(test.passages):
                    if p_idx < passage_index:
                        question_number += len(passage.questions)
                    elif p_idx == passage_index:
                        question_number += question_index + 1
                        break

            message = StudentProgressMessage(
                session_id=attempt.session_id,
                student_id=attempt.student_id,
                student_name=student_name,
                passage_index=passage_index,
                question_index=question_index,
                question_number=question_number,
                timestamp=TimeHelper.utc_now(),
            )

            await self.broadcaster.broadcast_student_activity(
                session_id=attempt.session_id,
                student_id=attempt.student_id,
                message=message.dict(),
            )
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to broadcast progress activity: {e}")
