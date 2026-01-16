from app.application.services.query.attempts.attempt_query_service import (
    AttemptQueryService,
)
from app.application.use_cases.attempts.queries.get_by_id.get_by_id_dto import (
    AnswerDTO,
    CurrentProgress,
    GetAttemptByIdQuery,
    GetAttemptByIdResponse,
    TestInfo,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.class_ import Class
from app.domain.aggregates.session import Session
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.attempt_errors import AttemptNotFoundError
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import (
    NoPermissionToViewSessionError,
    SessionNotFoundError,
)
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.persistence.models import UserModel


class GetAttemptByIdUseCase(
    AuthenticatedUseCase[GetAttemptByIdQuery, GetAttemptByIdResponse]
):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        attempt_query_service: AttemptQueryService,
    ):
        self.user_repo = user_repo
        self.attempt_query_service = attempt_query_service

    async def execute(
        self, request: GetAttemptByIdQuery, user_id: str
    ) -> GetAttemptByIdResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        attempt = await self.attempt_query_service.get_attempt_by_id(request.id)
        if attempt is None:
            raise AttemptNotFoundError(request.id)

        session = attempt.session
        if session is None:
            raise SessionNotFoundError(attempt.session_id)

        class_ = attempt.class_
        if class_ is None:
            raise ClassNotFoundError(attempt.class_id)

        test = attempt.test
        if test is None:
            raise TestNotFoundError(attempt.test_id)

        self._validate_user_permission(user, attempt.student_id, session, class_)

        time_remaining_seconds = TimeHelper.utc_now() - attempt.started_at

        return GetAttemptByIdResponse(
            id=attempt.id,
            session_id=session.id,
            test_id=test.id,
            student_id=attempt.student_id,
            status=attempt.status,
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            time_remaining_seconds=int(time_remaining_seconds.total_seconds()),
            test_info=TestInfo(
                id=test.id,
                title=test.title,
                test_type=test.test_type,
                time_limit_minutes=test.time_limit_minutes,
                passage_count=len(test.passage_ids),
            ),
            current_progress=CurrentProgress(
                passage_index=attempt.current_passage_index,
                question_index=attempt.current_question_index,
                total_questions=test.total_questions,
                answer_count=len(attempt.answers),
            ),
            answers=[
                AnswerDTO(
                    question_id=answer.question_id,
                    student_answer=answer.student_answer,
                )
                for answer in attempt.answers
            ],
            highlights=attempt.highlighted_text,
            violations=attempt.violations,
        )

    def _validate_user_permission(
        self, user: UserModel, student_id: str, session: Session, class_: Class
    ):
        if user.role == UserRole.ADMIN:
            return

        if user.role == UserRole.TEACHER and user.id not in class_.teacher_ids:
            raise NoPermissionToViewSessionError(user.id, session.id)

        if user.role == UserRole.STUDENT and student_id != user.id:
            raise NoPermissionToViewSessionError(user.id, session.id)

        return
