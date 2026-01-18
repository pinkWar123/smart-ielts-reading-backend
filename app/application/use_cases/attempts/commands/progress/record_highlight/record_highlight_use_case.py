from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_dto import (
    RecordHighlightRequest,
    RecordHighlightResponse,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface


class RecordHighlightUseCase(
    AuthenticatedUseCase[RecordHighlightRequest, RecordHighlightResponse]
):
    """
    Use case for recording text highlights during an attempt.

    Business rules:
    - Only students can record highlights in their own attempts
    - Attempt must be IN_PROGRESS status
    - Highlights are saved immediately to database
    - Students can have multiple overlapping highlights
    - Consider rate limiting: max 100 highlights per attempt (not enforced here)
    """

    MAX_HIGHLIGHTS_PER_ATTEMPT = 100

    def __init__(self, attempt_repo: AttemptRepositoryInterface):
        self.attempt_repo = attempt_repo

    async def execute(
        self, request: RecordHighlightRequest, user_id: str
    ) -> RecordHighlightResponse:
        attempt = await self._validate_and_get_attempt(request.attempt_id, user_id)

        # Check if max highlights reached
        if attempt.get_highlight_count() >= self.MAX_HIGHLIGHTS_PER_ATTEMPT:
            raise ValueError(
                f"Maximum number of highlights ({self.MAX_HIGHLIGHTS_PER_ATTEMPT}) reached for this attempt"
            )

        # Record highlight in domain model
        # Map color name to hex code (default yellow)
        color_map = {
            "yellow": "#FFFF00",
            "green": "#00FF00",
            "blue": "#0000FF",
            "red": "#FF0000",
            "orange": "#FFA500",
            "pink": "#FFC0CB",
        }
        color_code = color_map.get(request.color or "yellow", "#FFFF00")

        attempt.record_text_highlight(
            text=request.text,
            passage_id=request.passage_id,
            start=request.position_start,
            end=request.position_end,
            color_code=color_code,
        )

        # Persist to database
        updated_attempt = await self.attempt_repo.update(attempt)

        # Get the last highlight that was just added
        last_highlight = updated_attempt.highlighted_text[-1]

        return RecordHighlightResponse(
            id=last_highlight.id,
            text=last_highlight.text,
            passage_id=last_highlight.passage_id,
            position_start=last_highlight.position_start,
            position_end=last_highlight.position_end,
            color=request.color or "yellow",
            timestamp=last_highlight.timestamp,
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
