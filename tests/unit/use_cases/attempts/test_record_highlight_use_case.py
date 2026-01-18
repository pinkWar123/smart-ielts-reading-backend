from unittest.mock import AsyncMock

import pytest

from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_dto import (
    RecordHighlightRequest,
    RecordHighlightResponse,
)
from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_use_case import (
    RecordHighlightUseCase,
)
from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.errors.attempt_errors import (
    AttemptNotFoundError,
    InvalidAttemptStatusError,
    NoPermissionToUpdateAttemptError,
)


class TestRecordHighlightUseCase:
    """Tests for RecordHighlightUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_attempt_repo(self):
        return AsyncMock()

    @pytest.fixture
    def use_case(self, mock_attempt_repo):
        return RecordHighlightUseCase(attempt_repo=mock_attempt_repo)

    @pytest.fixture
    def valid_request(self):
        return RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="This is a highlighted text",
            passage_id="passage_1",
            position_start=10,
            position_end=35,
            color="yellow",
        )

    @pytest.fixture
    def valid_attempt(self):
        return Attempt(
            id="valid_attempt_id",
            test_id="valid_test_id",
            student_id="valid_user_id",
            status=AttemptStatus.IN_PROGRESS,
            answers=[],
            highlighted_text=[],
        )

    @pytest.mark.asyncio
    async def test_execute_success(
        self, use_case, mock_attempt_repo, valid_request, valid_attempt
    ):
        """Test successful highlight recording"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(valid_request, user_id="valid_user_id")

        assert response.text == "This is a highlighted text"
        assert response.passage_id == "passage_1"
        assert response.position_start == 10
        assert response.position_end == 35
        assert response.color == "yellow"
        assert response.id is not None
        assert response.timestamp is not None
        mock_attempt_repo.get_by_id.assert_awaited_once_with("valid_attempt_id")
        mock_attempt_repo.update.assert_awaited_once()

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
    async def test_execute_multiple_highlights(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test adding multiple highlights to the same attempt"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        # First highlight
        request1 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="First highlight",
            passage_id="passage_1",
            position_start=0,
            position_end=15,
            color="yellow",
        )
        response1 = await use_case.execute(request1, user_id="valid_user_id")
        assert response1.text == "First highlight"

        # Second highlight
        request2 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Second highlight",
            passage_id="passage_1",
            position_start=20,
            position_end=36,
            color="green",
        )
        response2 = await use_case.execute(request2, user_id="valid_user_id")
        assert response2.text == "Second highlight"

        # Verify both highlights are in the attempt
        assert len(valid_attempt.highlighted_text) == 2

    @pytest.mark.asyncio
    async def test_execute_overlapping_highlights(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test adding overlapping highlights (should be allowed)"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        # First highlight
        request1 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Overlapping text one",
            passage_id="passage_1",
            position_start=10,
            position_end=30,
        )
        await use_case.execute(request1, user_id="valid_user_id")

        # Overlapping highlight
        request2 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Overlapping text two",
            passage_id="passage_1",
            position_start=20,
            position_end=40,
        )
        response2 = await use_case.execute(request2, user_id="valid_user_id")

        assert response2.position_start == 20
        assert response2.position_end == 40
        assert len(valid_attempt.highlighted_text) == 2

    @pytest.mark.asyncio
    async def test_execute_very_long_text(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test highlighting very long text (edge case)"""
        long_text = "A" * 5000  # Maximum length
        request = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text=long_text,
            passage_id="passage_1",
            position_start=0,
            position_end=5000,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        assert len(response.text) == 5000
        assert response.position_end == 5000

    @pytest.mark.asyncio
    async def test_execute_single_character_highlight(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test highlighting a single character (edge case)"""
        request = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="A",
            passage_id="passage_1",
            position_start=0,
            position_end=1,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        assert response.text == "A"
        assert response.position_start == 0
        assert response.position_end == 1

    @pytest.mark.asyncio
    async def test_execute_max_highlights_limit(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test error when maximum highlights limit is reached"""
        # Create attempt with 100 highlights (the maximum)
        for i in range(100):
            valid_attempt.record_text_highlight(
                text=f"Highlight {i}",
                passage_id="passage_1",
                start=i * 10,
                end=i * 10 + 5,
            )

        mock_attempt_repo.get_by_id.return_value = valid_attempt

        request = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="One too many",
            passage_id="passage_1",
            position_start=1000,
            position_end=1012,
        )

        with pytest.raises(ValueError, match="Maximum number of highlights"):
            await use_case.execute(request, user_id="valid_user_id")

    @pytest.mark.asyncio
    async def test_execute_different_passages(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test highlighting text in different passages"""
        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        # Highlight in passage 1
        request1 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Passage 1 highlight",
            passage_id="passage_1",
            position_start=0,
            position_end=19,
        )
        response1 = await use_case.execute(request1, user_id="valid_user_id")
        assert response1.passage_id == "passage_1"

        # Highlight in passage 2
        request2 = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Passage 2 highlight",
            passage_id="passage_2",
            position_start=0,
            position_end=19,
        )
        response2 = await use_case.execute(request2, user_id="valid_user_id")
        assert response2.passage_id == "passage_2"

        assert len(valid_attempt.highlighted_text) == 2

    @pytest.mark.asyncio
    async def test_execute_default_color(
        self, use_case, mock_attempt_repo, valid_attempt
    ):
        """Test that default color is used when not specified"""
        request = RecordHighlightRequest(
            attempt_id="valid_attempt_id",
            text="Text with default color",
            passage_id="passage_1",
            position_start=0,
            position_end=23,
            color=None,
        )

        mock_attempt_repo.get_by_id.return_value = valid_attempt
        mock_attempt_repo.update.return_value = valid_attempt

        response = await use_case.execute(request, user_id="valid_user_id")

        # Default color should be "yellow"
        assert response.color == "yellow"

    @pytest.mark.asyncio
    async def test_execute_invalid_position_range(self):
        """Test validation error when position_end <= position_start"""
        with pytest.raises(ValueError, match="position_end must be greater than"):
            RecordHighlightRequest(
                attempt_id="valid_attempt_id",
                text="Invalid range",
                passage_id="passage_1",
                position_start=100,
                position_end=50,  # Invalid: end < start
            )

    @pytest.mark.asyncio
    async def test_execute_equal_start_and_end_positions(self):
        """Test validation error when position_start == position_end"""
        with pytest.raises(ValueError, match="position_end must be greater than"):
            RecordHighlightRequest(
                attempt_id="valid_attempt_id",
                text="Equal positions",
                passage_id="passage_1",
                position_start=50,
                position_end=50,  # Invalid: start == end
            )
