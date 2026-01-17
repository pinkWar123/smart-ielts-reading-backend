from app.application.services.query.attempts.attempt_query_service import (
    AttemptQueryService,
)
from app.application.use_cases.attempts.queries.get_by_id.get_by_id_dto import (
    AnswerDTO,
    TestInfo,
)
from app.application.use_cases.attempts.queries.get_my_attempt.get_my_attempt_dto import (
    GetMyAttemptQuery,
    GetMyAttemptResponse,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.aggregates.session import Session
from app.domain.aggregates.test import Test
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.attempt_errors import UserNotAStudentError
from app.domain.errors.session_errors import SessionNotFoundError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class GetMyAttemptUseCase(
    AuthenticatedUseCase[GetMyAttemptQuery, GetMyAttemptResponse]
):
    def __init__(
        self,
        attempt_query_service: AttemptQueryService,
        attempt_repo: AttemptRepositoryInterface,
        session_repo: SessionRepositoryInterface,
        test_repo: TestRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.attempt_query_service = attempt_query_service
        self.attempt_repo = attempt_repo
        self.session_repo = session_repo
        self.test_repo = test_repo
        self.user_repo = user_repo

    async def execute(
        self, request: GetMyAttemptQuery, user_id: str
    ) -> GetMyAttemptResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if user.role != UserRole.STUDENT:
            raise UserNotAStudentError(user_id=user_id)

        session = await self.session_repo.get_by_id(request.session_id)
        if not session:
            raise SessionNotFoundError(session_id=request.session_id)

        attempt = await self.attempt_repo.get_by_student_and_session(
            student_id=user_id, session_id=request.session_id
        )
        test = await self.test_repo.get_by_id(session.test_id)
        if test is None:
            raise TestNotFoundError(session.test_id)

        if attempt is not None:
            return self._convert_to_response(attempt, test)

        new_attempt = Attempt(
            test_id=session.test_id,
            student_id=user_id,
            session_id=request.session_id,
            status=AttemptStatus.IN_PROGRESS,
            started_at=TimeHelper.utc_now(),
            submitted_at=None,
            time_remaining_seconds=None,  # This is a redundant field, can be calculated by the frontend
            answers=[],
            tab_violations=[],
            highlighted_text=[],
            total_correct_answers=0,
            band_score=0,
            current_passage_index=0,
            current_question_index=0,
        )

        created_attempt = await self.attempt_repo.create(new_attempt)

        return self._convert_to_response(created_attempt, test)

    def _convert_to_response(
        self, attempt: Attempt, test: Test
    ) -> GetMyAttemptResponse:
        return GetMyAttemptResponse(
            id=attempt.id,
            session_id=attempt.session_id,
            test_id=attempt.test_id,
            student_id=attempt.student_id,
            status=attempt.status,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            time_remaining_seconds=attempt.time_remaining_seconds,
            test_info=TestInfo(
                id=test.id,
                title=test.title,
                test_type=test.test_type,
                time_limit_minutes=test.time_limit_minutes,
                passage_count=len(test.passage_ids),
            ),
            current_progress=None,
            answers=[
                AnswerDTO(question_id=a.question_id, student_answer=a.student_answer)
                for a in attempt.answers
            ],
            highlights=attempt.highlighted_text,
            violations=attempt.tab_violations,
        )
