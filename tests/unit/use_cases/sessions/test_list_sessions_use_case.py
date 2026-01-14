"""Unit tests for ListSessionsUseCase - Organized by class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.queries.list_sessions.list_sessions_dto import (
    ListSessionsQuery,
)
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_use_case import (
    ListSessionsUseCase,
)
from app.domain.aggregates.session import Session, SessionStatus


class TestListSessionsUseCase:
    """Tests for ListSessionsUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository."""
        repo = MagicMock()
        repo.get_by_teacher = AsyncMock()
        repo.get_by_class = AsyncMock()
        repo.get_active_sessions = AsyncMock()
        return repo

    @pytest.fixture
    def use_case(self, mock_session_repo):
        """Create use case with mocked dependencies."""
        return ListSessionsUseCase(session_repo=mock_session_repo)

    @pytest.fixture
    def sample_sessions(self):
        """Create sample sessions."""
        now = datetime.utcnow()
        return [
            Session(
                id="session-1",
                class_id="class-001",
                test_id="test-001",
                title="Session 1",
                scheduled_at=now,
                status=SessionStatus.SCHEDULED,
                participants=[],
                created_by="teacher-123",
                created_at=now,
            ),
            Session(
                id="session-2",
                class_id="class-001",
                test_id="test-002",
                title="Session 2",
                scheduled_at=now,
                status=SessionStatus.WAITING_FOR_STUDENTS,
                participants=[],
                created_by="teacher-123",
                created_at=now,
            ),
            Session(
                id="session-3",
                class_id="class-002",
                test_id="test-003",
                title="Session 3",
                scheduled_at=now,
                status=SessionStatus.IN_PROGRESS,
                participants=[],
                created_by="teacher-456",
                created_at=now,
            ),
        ]

    @pytest.mark.asyncio
    async def test_list_sessions_by_teacher(
        self, use_case, mock_session_repo, sample_sessions
    ):
        """Test listing sessions filtered by teacher."""
        # Setup
        teacher_sessions = [sample_sessions[0], sample_sessions[1]]
        mock_session_repo.get_by_teacher.return_value = teacher_sessions

        query = ListSessionsQuery(teacher_id="teacher-123")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 2
        assert response.sessions[0].id == "session-1"
        assert response.sessions[1].id == "session-2"
        assert all(s.created_by == "teacher-123" for s in response.sessions)

        # Verify repository call
        mock_session_repo.get_by_teacher.assert_called_once_with("teacher-123")

    @pytest.mark.asyncio
    async def test_list_sessions_by_class(
        self, use_case, mock_session_repo, sample_sessions
    ):
        """Test listing sessions filtered by class."""
        # Setup
        class_sessions = [sample_sessions[0], sample_sessions[1]]
        mock_session_repo.get_by_class.return_value = class_sessions

        query = ListSessionsQuery(class_id="class-001")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 2
        assert all(s.class_id == "class-001" for s in response.sessions)

        # Verify repository call
        mock_session_repo.get_by_class.assert_called_once_with("class-001")

    @pytest.mark.asyncio
    async def test_list_active_sessions(
        self, use_case, mock_session_repo, sample_sessions
    ):
        """Test listing active sessions (no filters)."""
        # Setup
        active_sessions = [sample_sessions[1], sample_sessions[2]]
        mock_session_repo.get_active_sessions.return_value = active_sessions

        query = ListSessionsQuery()

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 2
        assert response.sessions[0].status == SessionStatus.WAITING_FOR_STUDENTS
        assert response.sessions[1].status == SessionStatus.IN_PROGRESS

        # Verify repository call
        mock_session_repo.get_active_sessions.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_sessions_empty_result(self, use_case, mock_session_repo):
        """Test listing sessions returns empty list when no sessions found."""
        # Setup
        mock_session_repo.get_by_teacher.return_value = []

        query = ListSessionsQuery(teacher_id="teacher-999")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 0
        assert response.sessions == []

    @pytest.mark.asyncio
    async def test_list_sessions_includes_participant_count(
        self, use_case, mock_session_repo
    ):
        """Test that session summary includes participant count."""
        # Setup - session with participants
        from app.domain.aggregates.session import SessionParticipant

        session_with_participants = Session(
            id="session-1",
            class_id="class-001",
            test_id="test-001",
            title="Session 1",
            scheduled_at=datetime.utcnow(),
            status=SessionStatus.SCHEDULED,
            participants=[
                SessionParticipant(
                    student_id="student-1",
                    connection_status="DISCONNECTED",
                ),
                SessionParticipant(
                    student_id="student-2",
                    connection_status="DISCONNECTED",
                ),
                SessionParticipant(
                    student_id="student-3",
                    connection_status="CONNECTED",
                ),
            ],
            created_by="teacher-123",
            created_at=datetime.utcnow(),
        )

        mock_session_repo.get_by_teacher.return_value = [session_with_participants]

        query = ListSessionsQuery(teacher_id="teacher-123")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 1
        assert response.sessions[0].participant_count == 3
