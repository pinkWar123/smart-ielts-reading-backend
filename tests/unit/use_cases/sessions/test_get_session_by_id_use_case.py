"""Unit tests for GetSessionByIdUseCase - Organized by class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_dto import (
    GetSessionByIdQuery,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_use_case import (
    GetSessionByIdUseCase,
)
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
from app.domain.errors.session_errors import SessionNotFoundError


class TestGetSessionByIdUseCase:
    """Tests for GetSessionByIdUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    @pytest.fixture
    def use_case(self, mock_session_repo):
        """Create use case with mocked dependencies."""
        return GetSessionByIdUseCase(session_repo=mock_session_repo)

    @pytest.fixture
    def sample_session(self):
        """Create sample session with participants."""
        now = datetime.utcnow()
        return Session(
            id="session-123",
            class_id="class-001",
            test_id="test-001",
            title="Monday Test",
            scheduled_at=now,
            status=SessionStatus.SCHEDULED,
            participants=[
                SessionParticipant(
                    student_id="student-1",
                    attempt_id=None,
                    joined_at=None,
                    connection_status="DISCONNECTED",
                    last_activity=None,
                ),
                SessionParticipant(
                    student_id="student-2",
                    attempt_id="attempt-456",
                    joined_at=now,
                    connection_status="CONNECTED",
                    last_activity=now,
                ),
            ],
            created_by="teacher-789",
            created_at=now,
            updated_at=now,
        )

    @pytest.mark.asyncio
    async def test_get_session_by_id_success(
        self, use_case, mock_session_repo, sample_session
    ):
        """Test successfully retrieving session by ID."""
        # Setup
        mock_session_repo.get_by_id.return_value = sample_session

        query = GetSessionByIdQuery(session_id="session-123")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert response.id == "session-123"
        assert response.class_id == "class-001"
        assert response.test_id == "test-001"
        assert response.title == "Monday Test"
        assert response.status == SessionStatus.SCHEDULED
        assert response.created_by == "teacher-789"

        # Verify participants
        assert len(response.participants) == 2
        assert response.participants[0].student_id == "student-1"
        assert response.participants[0].connection_status == "DISCONNECTED"
        assert response.participants[1].student_id == "student-2"
        assert response.participants[1].connection_status == "CONNECTED"
        assert response.participants[1].attempt_id == "attempt-456"

        # Verify repository call
        mock_session_repo.get_by_id.assert_called_once_with("session-123")

    @pytest.mark.asyncio
    async def test_get_session_by_id_not_found(self, use_case, mock_session_repo):
        """Test error when session doesn't exist."""
        # Setup
        mock_session_repo.get_by_id.return_value = None

        query = GetSessionByIdQuery(session_id="non-existent")

        # Execute & Assert
        with pytest.raises(SessionNotFoundError) as exc_info:
            await use_case.execute(query)

        assert "non-existent" in str(exc_info.value)
        mock_session_repo.get_by_id.assert_called_once_with("non-existent")

    @pytest.mark.asyncio
    async def test_get_session_by_id_includes_all_fields(
        self, use_case, mock_session_repo
    ):
        """Test that all session fields are included in response."""
        # Setup - session with all fields populated
        now = datetime.utcnow()
        complete_session = Session(
            id="session-999",
            class_id="class-999",
            test_id="test-999",
            title="Complete Session",
            scheduled_at=now,
            started_at=now,
            completed_at=now,
            status=SessionStatus.COMPLETED,
            participants=[
                SessionParticipant(
                    student_id="student-999",
                    attempt_id="attempt-999",
                    joined_at=now,
                    connection_status="DISCONNECTED",
                    last_activity=now,
                ),
            ],
            created_by="teacher-999",
            created_at=now,
            updated_at=now,
        )

        mock_session_repo.get_by_id.return_value = complete_session

        query = GetSessionByIdQuery(session_id="session-999")

        # Execute
        response = await use_case.execute(query)

        # Assert all fields are present
        assert response.id == "session-999"
        assert response.class_id == "class-999"
        assert response.test_id == "test-999"
        assert response.title == "Complete Session"
        assert response.scheduled_at == now
        assert response.started_at == now
        assert response.completed_at == now
        assert response.status == SessionStatus.COMPLETED
        assert response.created_by == "teacher-999"
        assert response.created_at == now
        assert response.updated_at == now

        # Assert participant fields
        participant = response.participants[0]
        assert participant.student_id == "student-999"
        assert participant.attempt_id == "attempt-999"
        assert participant.joined_at == now
        assert participant.connection_status == "DISCONNECTED"
        assert participant.last_activity == now

    @pytest.mark.asyncio
    async def test_get_session_by_id_empty_participants(
        self, use_case, mock_session_repo
    ):
        """Test retrieving session with no participants."""
        # Setup
        session_no_participants = Session(
            id="session-empty",
            class_id="class-001",
            test_id="test-001",
            title="Empty Session",
            scheduled_at=datetime.utcnow(),
            status=SessionStatus.SCHEDULED,
            participants=[],
            created_by="teacher-123",
            created_at=datetime.utcnow(),
        )

        mock_session_repo.get_by_id.return_value = session_no_participants

        query = GetSessionByIdQuery(session_id="session-empty")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert response.id == "session-empty"
        assert len(response.participants) == 0
        assert response.participants == []
