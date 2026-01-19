from typing import Optional

from app.application.services.query.tests.test_query_model import (
    TestWithPassagesQueryModel,
)
from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.services.websocket_broadcaster_service import (
    WebSocketBroadcasterService,
)
from app.application.use_cases.attempts.commands.progress.update_answer.update_answer_dto import (
    UpdateAnswerRequest,
    UpdateAnswerResponse,
)
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.attempt.attempt import Answer, Attempt, AttemptStatus
from app.domain.aggregates.passage.question import Question
from app.domain.aggregates.test import TestStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.errors.question_errors import QuestionDoesNotBelongToTestError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.domain.repositories.question_repository import QuestionRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.web_socket.message_types import StudentAnswerMessage


class UpdateAnswerUseCase(
    AuthenticatedUseCase[UpdateAnswerRequest, UpdateAnswerResponse]
):
    def __init__(
        self,
        test_query_service: TestQueryService,
        attempt_repo: AttemptRepositoryInterface,
        user_repo: UserRepositoryInterface,
        broadcaster: Optional[WebSocketBroadcasterService] = None,
    ):
        self.test_query_service = test_query_service
        self.attempt_repo = attempt_repo
        self.user_repo = user_repo
        self.broadcaster = broadcaster

    async def execute(
        self, request: UpdateAnswerRequest, user_id: str
    ) -> UpdateAnswerResponse:
        attempt = await self._validate_and_get_attempt(request.attempt_id, user_id)
        test = await self._validate_and_get_test(attempt)
        question = self._validate_and_get_question(request.question_id, test)

        answer = self._create_answer(request)
        is_update = any(a.question_id == request.question_id for a in attempt.answers)
        attempt.submit_answer(answer)

        updated_attempt = await self.attempt_repo.update(attempt)

        # Broadcast to teachers if part of a session
        if updated_attempt.session_id and self.broadcaster:
            await self._broadcast_answer_activity(
                attempt=updated_attempt,
                question=question,
                is_update=is_update,
            )

        return UpdateAnswerResponse(
            question_id=request.question_id,
            question_number=question.question_number,
            answer=request.answer,
            is_updated=True,
            submitted_at=updated_attempt.submitted_at,
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

    async def _validate_and_get_test(
        self, attempt: Attempt
    ) -> TestWithPassagesQueryModel:
        """Validate test exists and is published."""
        test = await self.test_query_service.get_test_by_id_with_passages(
            test_id=attempt.test_id, status=TestStatus.PUBLISHED, test_type=None
        )
        if not test:
            raise TestNotFoundError(attempt.test_id)

        return test

    def _validate_and_get_question(
        self, question_id: str, test: TestWithPassagesQueryModel
    ) -> Question:
        """Validate question exists in test."""
        questions_by_id = {
            q.id: q for passage in test.passages for q in passage.questions
        }
        question = questions_by_id.get(question_id)
        if not question:
            raise QuestionDoesNotBelongToTestError(question_id, test_id=test.id)

        return question

    def _create_answer(self, request: UpdateAnswerRequest) -> Answer:
        """Create an Answer domain object from the request."""
        return Answer(
            question_id=request.question_id,
            student_answer=request.answer,
            is_correct=False,  # This is false, because we will calculate it later
            answered_at=TimeHelper.utc_now(),
        )

    async def _broadcast_answer_activity(
        self, attempt: Attempt, question: Question, is_update: bool
    ) -> None:
        """Broadcast student answer activity to teachers."""
        try:
            # Get student name
            student = await self.user_repo.get_by_id(attempt.student_id)
            student_name = student.full_name if student else "Unknown Student"

            message = StudentAnswerMessage(
                session_id=attempt.session_id,
                student_id=attempt.student_id,
                student_name=student_name,
                question_id=question.id,
                question_number=question.question_number,
                answered=True,
                is_update=is_update,
                timestamp=TimeHelper.utc_now(),
            )

            await self.broadcaster.broadcast_student_activity(
                session_id=attempt.session_id,
                student_id=attempt.student_id,
                message=message.model_dump(mode="json"),
            )
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Failed to broadcast answer activity: {e}")
