from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.attempts.commands.progress.update_progress.update_progress_dto import (
    UpdateProgressRequest,
    UpdateProgressResponse,
)
from app.application.use_cases.attempts.commands.progress.update_progress.update_progress_use_case import (
    UpdateProgressUseCase,
)
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)


class TestUpdateProgressUseCase:
    """Tests for UpdateProgressUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_attempt_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_attempt_repo):
        return UpdateProgressUseCase(attempt_repo=mock_attempt_repo)

    @pytest.fixture
    def valid_request(self):
        return UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=2,
            question_index=5,
            passage_id="passage_1",
            question_id="question_1",
        )

    @pytest.fixture
    def valid_attempt(self):
        return Attempt(
            id="valid_attempt_id",
            test_id="valid_test_id",
            student_id="valid_user_id",
            status=AttemptStatus.IN_PROGRESS,
            answers=[],
            current_passage_index=0,
            current_question_index=0,
        )

    @pytest.mark.asyncio
    async def test_execute_success(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        """Test successful progress update"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(valid_request, user_id="valid_user_id")

        assert response.passage_index == 2
        assert response.question_index == 5
        assert response.updated_at is not None
        mock_attempt_repo.get_by_id.assert_awaited_once_with("valid_attempt_id")
        mock_attempt_repo.update.assert_awaited_once()

        # Verify the attempt was updated
        updated_attempt = mock_attempt_repo.update.call_args[0][0]
        assert updated_attempt.current_passage_index == 2
        assert updated_attempt.current_question_index == 5

    @pytest.mark.asyncio
    async def test_execute_attempt_not_found(
        self, use_case, mock_attempt_repo, valid_request
    ):
        """Test error when attempt doesn't exist"""
        mock_attempt_repo.get_by_id.return_value = None

        with pytest.raises(AttemptNotFoundError):
            await use_case.execute(valid_request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_no_permission(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        """Test error when user doesn't own the attempt"""
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
    async def test_execute_progress_at_zero(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test updating progress to the beginning (edge case)"""
        request = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=0,
            question_index=0,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        assert response.passage_index == 0
        assert response.question_index == 0

    @pytest.mark.asyncio
    async def test_execute_progress_large_indices(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test updating progress with large indices"""
        request = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=99,
            question_index=999,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        assert response.passage_index == 99
        assert response.question_index == 999

    @pytest.mark.asyncio
    async def test_execute_progress_without_optional_ids(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test updating progress without passage_id and question_id"""
        request = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=1,
            question_index=3,
            passage_id=None,
            question_id=None,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        assert response.passage_index == 1
        assert response.question_index == 3

    @pytest.mark.asyncio
    async def test_execute_multiple_progress_updates(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test multiple sequential progress updates"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        # First update
        request1 = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=1,
            question_index=0,
        )
        response1 = await use_case.execute(request1, user_id="valid_user_id")
        assert response1.passage_index == 1
        assert response1.question_index == 0

        # Second update
        request2 = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=1,
            question_index=5,
        )
        response2 = await use_case.execute(request2, user_id="valid_user_id")
        assert response2.passage_index == 1
        assert response2.question_index == 5

        # Third update
        request3 = UpdateProgressRequest(
            attempt_id="valid_attempt_id",
            passage_index=2,
            question_index=0,
        )
        response3 = await use_case.execute(request3, user_id="valid_user_id")
        assert response3.passage_index == 2
        assert response3.question_index == 0

        # Verify repository was called three times
        assert mock_attempt_repo.update.await_count == 3
