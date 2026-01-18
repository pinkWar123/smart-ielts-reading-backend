from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.attempts.commands.submit.submit_attempt_dto import (
    SubmitAttemptRequest,
    SubmitAttemptResponse,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.domain.aggregates.attempt.attempt import AttemptStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.errors.question_errors import QuestionNotFoundError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface


class SubmitAttemptUseCase(
    AuthenticatedUseCase[SubmitAttemptRequest, SubmitAttemptResponse]
):

    def __init__(
        self,
        attempt_repo: AttemptRepositoryInterface,
        test_query_service: TestQueryService,
    ):
        self.attempt_repo = attempt_repo
        self.test_query_service = test_query_service

    async def execute(
        self, request: SubmitAttemptRequest, user_id: str
    ) -> SubmitAttemptResponse:
        attempt = await self.attempt_repo.get_by_id(request.attempt_id)
        if not attempt:
            raise AttemptNotFoundError(request.attempt_id)
        if attempt.student_id != user_id:
            raise NoPermissionToUpdateAttemptError(user_id)
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStatusError(request.attempt_id, attempt.status)

        test = await self.test_query_service.get_test_by_id_with_passages(
            attempt.test_id
        )
        if not test:
            raise TestNotFoundError(attempt.test_id)
        test_questions = [
            question for passage in test.passages for question in passage.questions
        ]
        test_questions_by_id = {question.id: question for question in test_questions}
        for answer in attempt.answers:
            question_id = answer.question_id
            if question_id not in test_questions_by_id:
                raise QuestionNotFoundError(question_id)
            question = test_questions_by_id[question_id]
            if question.correct_answer.is_correct(answer.student_answer):
                answer.is_correct = True
            else:
                answer.is_correct = False

        # Calculate scores using domain logic
        attempt.total_correct_answers = attempt.get_correct_answers_count()
        attempt.band_score = attempt.calculate_band_score()
        attempt.submit_attempt(request.submit_type)
        attempt = await self.attempt_repo.update(attempt)
        return SubmitAttemptResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            submitted_at=attempt.submitted_at,
            score=attempt.band_score,
            total_questions=len(test_questions),
            answered_questions=len(attempt.answers),
            time_taken_seconds=test.time_limit_minutes * 60
            - attempt.time_remaining_seconds,
            answers=attempt.answers,
        )
