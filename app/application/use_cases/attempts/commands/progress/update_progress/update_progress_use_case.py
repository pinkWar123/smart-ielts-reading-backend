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


class UpdateProgressUseCase(
    AuthenticatedUseCase[UpdateProgressRequest, UpdateProgressResponse]
):
    """
    Use case for updating student's progress in an attempt.

    Business rules:
    - Only students can update their own attempt progress
    - Attempt must be IN_PROGRESS status
    - Progress is immediately persisted to database for reconnection support
    - Client should debounce progress updates (e.g., max 1 update per 2 seconds)
    """

    def __init__(self, attempt_repo: AttemptRepositoryInterface):
        self.attempt_repo = attempt_repo

    async def execute(
        self, request: UpdateProgressRequest, user_id: str
    ) -> UpdateProgressResponse:
        attempt = await self._validate_and_get_attempt(request.attempt_id, user_id)

        # Update progress in domain model
        attempt.update_progress(request.passage_index, request.question_index)

        # Persist to database
        await self.attempt_repo.update(attempt)

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
