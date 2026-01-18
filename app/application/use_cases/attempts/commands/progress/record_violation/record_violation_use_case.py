from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple

from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.attempts.commands.progress.record_violation.record_violation_dto import (
    RecordViolationRequest,
    RecordViolationResponse,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.aggregates.attempt.violation_type import ViolationType
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.infrastructure.web_socket.message_types import ViolationRecordedMessage


class RecordViolationUseCase(
    AuthenticatedUseCase[RecordViolationRequest, RecordViolationResponse]
):
    """
    Use case for recording violations during an attempt.

    Business rules:
    - Only students can record violations in their own attempts
    - Attempt must be IN_PROGRESS status
    - Violations are recorded immediately
    - Rate limiting: max 1 violation per second per type (prevent spam)
    - Broadcasts to teacher via WebSocket if part of a session
    """

    # Class-level rate limiting: {(attempt_id, violation_type): last_timestamp}
    _rate_limit_tracker: Dict[Tuple[str, str], datetime] = {}
    RATE_LIMIT_SECONDS = 1

    def __init__(
        self,
        attempt_repo: AttemptRepositoryInterface,
        connection_manager: ConnectionManagerServiceInterface,
    ):
        self.attempt_repo = attempt_repo
        self.connection_manager = connection_manager

    async def execute(
        self, request: RecordViolationRequest, user_id: str
    ) -> RecordViolationResponse:
        attempt = await self._validate_and_get_attempt(request.attempt_id, user_id)

        # Check rate limiting
        self._check_rate_limit(request.attempt_id, request.violation_type)

        # Record violation in domain model
        attempt.record_tab_violation(
            violation_type=request.violation_type,
            metadata=request.metadata,
        )

        # Persist to database
        updated_attempt = await self.attempt_repo.update(attempt)

        # Get the last violation that was just added
        last_violation = updated_attempt.tab_violations[-1]
        total_violations = updated_attempt.get_violation_count()

        # Broadcast to teacher via WebSocket if part of a session
        if updated_attempt.session_id:
            await self._broadcast_violation_to_teacher(
                session_id=updated_attempt.session_id,
                student_id=updated_attempt.student_id,
                violation_type=request.violation_type.value,
                timestamp=last_violation.timestamp,
                total_count=total_violations,
            )

        return RecordViolationResponse(
            violation_type=last_violation.violation_type,
            timestamp=last_violation.timestamp,
            total_violations=total_violations,
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

    def _check_rate_limit(self, attempt_id: str, violation_type: ViolationType) -> None:
        """
        Check if violation is being submitted too quickly (spam prevention).

        Raises:
            ValueError: If rate limit is exceeded
        """
        rate_key = (attempt_id, violation_type.value)
        now = TimeHelper.utc_now()

        if rate_key in self._rate_limit_tracker:
            last_time = self._rate_limit_tracker[rate_key]
            time_since_last = (now - last_time).total_seconds()

            if time_since_last < self.RATE_LIMIT_SECONDS:
                raise ValueError(
                    f"Rate limit exceeded. Please wait {self.RATE_LIMIT_SECONDS - time_since_last:.1f}s before recording another {violation_type.value} violation."
                )

        # Update tracker with current time
        self._rate_limit_tracker[rate_key] = now

        # Clean up old entries (older than 10 seconds)
        cutoff_time = now - timedelta(seconds=10)
        self._rate_limit_tracker = {
            k: v for k, v in self._rate_limit_tracker.items() if v > cutoff_time
        }

    async def _broadcast_violation_to_teacher(
        self,
        session_id: str,
        student_id: str,
        violation_type: str,
        timestamp: datetime,
        total_count: int,
    ) -> None:
        """Broadcast violation event to teacher via WebSocket."""
        try:
            message = ViolationRecordedMessage(
                student_id=student_id,
                violation_type=violation_type,
                timestamp=timestamp,
                total_count=total_count,
            )
            await self.connection_manager.broadcast_to_session(
                session_id=session_id,
                message=message.dict(),
            )
        except Exception as e:
            # Log error but don't fail the violation recording
            # WebSocket failures should not prevent violation tracking
            print(f"Failed to broadcast violation to teacher: {e}")
