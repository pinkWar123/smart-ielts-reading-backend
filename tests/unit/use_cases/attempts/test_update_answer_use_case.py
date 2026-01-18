from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.attempts.commands.progress.update_answer.update_answer_dto import (
    UpdateAnswerRequest,
    UpdateAnswerResponse,
)
from app.application.use_cases.attempts.commands.progress.update_answer.update_answer_use_case import (
    UpdateAnswerUseCase,
)
from app.domain.aggregates.attempt.attempt import Answer, Attempt, AttemptStatus
from app.domain.aggregates.test import TestStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)
from app.domain.errors.question_errors import QuestionDoesNotBelongToTestError
from app.domain.errors.test_errors import TestNotFoundError


class TestUpdateAnswerUseCase:
    """Tests for UpdateAnswerUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_test_query_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_attempt_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_test_query_service, mock_attempt_repo):
        return UpdateAnswerUseCase(
            test_query_service=mock_test_query_service,
            attempt_repo=mock_attempt_repo,
        )

    @pytest.fixture
    def valid_request(self):
        return UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="valid_question_id",
            answer="Valid Answer",
        )

    @pytest.fixture
    def valid_attempt(self):
        return Attempt(
            id="valid_attempt_id",
            test_id="valid_test_id",
            student_id="valid_user_id",
            status=AttemptStatus.IN_PROGRESS,
            answers=[],
        )

    @pytest.fixture
    def valid_test(self):
        class MockQuestion:
            id = "valid_question_id"
            question_number = 1
            question_text = "Sample question?"

        class MockPassage:
            id = "passage_1"
            questions = [MockQuestion()]

        class MockTest:
            id = "valid_test_id"
            passages = [MockPassage()]

        return MockTest()

    @pytest.fixture
    def valid_response(self):
        return UpdateAnswerResponse(
            question_id="valid_question_id",
            question_number=1,
            answer="Valid Answer",
            is_updated=True,
            submitted_at=None,
        )

    @pytest.mark.asyncio
    async def test_execute_success(
        self,
        use_case,
        mock_test_query_service,
        mock_attempt_repo,
        valid_request,
        valid_attempt,
        valid_test,
    ):
        """Test successful answer submission"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(valid_request, user_id="valid_user_id")

        assert response.question_id == "valid_question_id"
        assert response.answer == "Valid Answer"
        assert response.is_updated is True
        assert response.question_number == 1
        mock_attempt_repo.get_by_id.assert_awaited_once_with("valid_attempt_id")
        mock_test_query_service.get_test_by_id_with_passages.assert_awaited_once_with(
            test_id="valid_test_id",
            status=TestStatus.PUBLISHED,
            test_type=None,
        )
        mock_attempt_repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_attempt_not_found(
        self, use_case, mock_attempt_repo, valid_request
    ):
        mock_attempt_repo.get_by_id.return_value = None

        with pytest.raises(AttemptNotFoundError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_no_permission(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        valid_attempt.student_id = "other_user_id"
        mock_attempt_repo.get_by_id.return_value = valid_attempt

        with pytest.raises(NoPermissionToUpdateAttemptError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_invalid_attempt_status_submitted(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        """Test error when attempt is already submitted"""
        valid_attempt.status = AttemptStatus.SUBMITTED
        mock_attempt_repo.get_by_id.return_value = valid_attempt

        with pytest.raises(InvalidAttemptStatusError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_invalid_attempt_status_abandoned(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        """Test error when attempt is abandoned"""
        valid_attempt.status = AttemptStatus.ABANDONED
        mock_attempt_repo.get_by_id.return_value = valid_attempt

        with pytest.raises(InvalidAttemptStatusError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_test_not_found(
        self,
        use_case,
        mock_attempt_repo,
        mock_test_query_service,
        valid_request,
        valid_attempt,
    ):
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = None

        with pytest.raises(TestNotFoundError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_question_not_belong_to_test(
        self,
        use_case,
        mock_attempt_repo,
        mock_test_query_service,
        valid_request,
        valid_attempt,
        valid_test,
    ):
        """Test error when question doesn't belong to the test"""
        valid_test.passages = []

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test

        with pytest.raises(QuestionDoesNotBelongToTestError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_student_updates_existing_answer(
        self,
        use_case,
        mock_test_query_service,
        mock_attempt_repo,
        valid_test,
    ):
        """Test updating an existing answer - should replace the old answer"""
        # Create attempt with an existing answer
        existing_answer = Answer(
            question_id="valid_question_id",
            student_answer="Old Answer",
            is_correct=False,
            answered_at=datetime(2024, 1, 1, 10, 0, 0),
        )
        attempt_with_answer = Attempt(
            id="valid_attempt_id",
            test_id="valid_test_id",
            student_id="valid_user_id",
            status=AttemptStatus.IN_PROGRESS,
            answers=[existing_answer],
        )

        new_request = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="valid_question_id",
            answer="Updated Answer",
        )

        mock_attempt_repo.get_by_id.return_value = attempt_with_answer
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test
        mock_attempt_repo.update.return_value = attempt_with_answer

        response = await use_case.execute(new_request, user_id="valid_user_id")

        # Verify the response
        assert response.question_id == "valid_question_id"
        assert response.answer == "Updated Answer"
        assert response.is_updated is True

        # Verify that the attempt was updated
        mock_attempt_repo.update.assert_awaited_once()
        updated_attempt = mock_attempt_repo.update.call_args[0][0]

        # Should have only one answer (the old one was replaced)
        assert len(updated_attempt.answers) == 1
        assert updated_attempt.answers[0].question_id == "valid_question_id"
        assert updated_attempt.answers[0].student_answer == "Updated Answer"

    @pytest.mark.asyncio
    async def test_execute_student_answers_multiple_questions(
        self,
        use_case,
        mock_test_query_service,
        mock_attempt_repo,
    ):
        """Test submitting answers to multiple different questions"""

        # Create test with multiple questions
        class MockQuestion1:
            id = "question_1"
            question_number = 1
            question_text = "Question 1?"

        class MockQuestion2:
            id = "question_2"
            question_number = 2
            question_text = "Question 2?"

        class MockPassage:
            id = "passage_1"
            questions = [MockQuestion1(), MockQuestion2()]

        class MockTest:
            id = "valid_test_id"
            passages = [MockPassage()]

        test = MockTest()

        # Start with empty attempt
        attempt = Attempt(
            id="valid_attempt_id",
            test_id="valid_test_id",
            student_id="valid_user_id",
            status=AttemptStatus.IN_PROGRESS,
            answers=[],
        )

        mock_attempt_repo.get_by_id.return_value = attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = test
        mock_attempt_repo.update.return_value = attempt

        # Answer first question
        request1 = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="question_1",
            answer="Answer 1",
        )
        await use_case.execute(request1, user_id="valid_user_id")

        # Answer second question
        request2 = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="question_2",
            answer="Answer 2",
        )
        await use_case.execute(request2, user_id="valid_user_id")

        # Verify both answers are stored
        assert len(attempt.answers) == 2
        assert any(
            a.question_id == "question_1" and a.student_answer == "Answer 1"
            for a in attempt.answers
        )
        assert any(
            a.question_id == "question_2" and a.student_answer == "Answer 2"
            for a in attempt.answers
        )

    @pytest.mark.asyncio
    async def test_execute_empty_answer_string(
        self,
        use_case,
        mock_test_query_service,
        mock_attempt_repo,
        valid_attempt,
        valid_test,
    ):
        """Test submitting an empty answer (edge case)"""
        empty_request = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="valid_question_id",
            answer="",
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(empty_request, user_id="valid_user_id")

        assert response.answer == ""
        assert response.is_updated is True

    @pytest.mark.asyncio
    async def test_execute_very_long_answer(
        self,
        use_case,
        mock_test_query_service,
        mock_attempt_repo,
        valid_attempt,
        valid_test,
    ):
        """Test submitting a very long answer (edge case)"""
        long_answer = "A" * 10000  # 10,000 characters
        long_request = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="valid_question_id",
            answer=long_answer,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(long_request, user_id="valid_user_id")

        assert response.answer == long_answer
        assert response.is_updated is True

    @pytest.mark.asyncio
    async def test_execute_question_id_from_different_test(
        self,
        use_case,
        mock_attempt_repo,
        mock_test_query_service,
        valid_attempt,
        valid_test,
    ):
        """Test error when trying to answer a question from a different test"""
        wrong_question_request = UpdateAnswerRequest(
            attempt_id="valid_attempt_id",
            question_id="question_from_different_test",
            answer="Some answer",
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_test_query_service.get_test_by_id_with_passages.return_value = valid_test

        with pytest.raises(QuestionDoesNotBelongToTestError):
            await use_case.execute(wrong_question_request, user_id="valid_user_id")
