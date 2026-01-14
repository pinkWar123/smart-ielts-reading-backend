"""Unit tests for GetMySessionsUseCase - Organized by class."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_dto import (
    GetMySessionsQuery,
)
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_use_case import (
    GetMySessionsUseCase,
)
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus


class TestGetMySessionsUseCase:
    """Tests for GetMySessionsUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository."""
        repo = MagicMock()
        repo.get_by_student = AsyncMock()
        return repo

    @pytest.fixture
    def use_case(self, mock_session_repo):
        """Create use case with mocked dependencies."""
        return GetMySessionsUseCase(session_repo=mock_session_repo)

    @pytest.mark.asyncio
    async def test_get_my_sessions_success(self, use_case, mock_session_repo):
        """Test successfully retrieving student's sessions."""
        # Setup
        now = datetime.utcnow()
        student_id = "student-123"

        sessions = [
            Session(
                id="session-1",
                class_id="class-001",
                test_id="test-001",
                title="Session 1",
                scheduled_at=now,
                status=SessionStatus.SCHEDULED,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        attempt_id=None,
                        joined_at=None,
                        connection_status="DISCONNECTED",
                        last_activity=None,
                    ),
                    SessionParticipant(
                        student_id="student-456",
                        connection_status="DISCONNECTED",
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
            Session(
                id="session-2",
                class_id="class-002",
                test_id="test-002",
                title="Session 2",
                scheduled_at=now,
                started_at=now,
                status=SessionStatus.IN_PROGRESS,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        attempt_id="attempt-999",
                        joined_at=now,
                        connection_status="CONNECTED",
                        last_activity=now,
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
        ]

        mock_session_repo.get_by_student.return_value = sessions

        query = GetMySessionsQuery(student_id=student_id)

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 2

        # Check first session
        session1 = response.sessions[0]
        assert session1.id == "session-1"
        assert session1.class_id == "class-001"
        assert session1.test_id == "test-001"
        assert session1.title == "Session 1"
        assert session1.status == SessionStatus.SCHEDULED
        assert session1.my_attempt_id is None
        assert session1.my_joined_at is None
        assert session1.my_connection_status == "DISCONNECTED"

        # Check second session
        session2 = response.sessions[1]
        assert session2.id == "session-2"
        assert session2.status == SessionStatus.IN_PROGRESS
        assert session2.my_attempt_id == "attempt-999"
        assert session2.my_joined_at == now
        assert session2.my_connection_status == "CONNECTED"

        # Verify repository call
        mock_session_repo.get_by_student.assert_called_once_with(student_id)

    @pytest.mark.asyncio
    async def test_get_my_sessions_empty_result(self, use_case, mock_session_repo):
        """Test retrieving sessions when student has no sessions."""
        # Setup
        mock_session_repo.get_by_student.return_value = []

        query = GetMySessionsQuery(student_id="student-999")

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 0
        assert response.sessions == []

    @pytest.mark.asyncio
    async def test_get_my_sessions_filters_student_info(
        self, use_case, mock_session_repo
    ):
        """Test that only the requesting student's info is included."""
        # Setup
        now = datetime.utcnow()
        student_id = "student-123"

        session = Session(
            id="session-1",
            class_id="class-001",
            test_id="test-001",
            title="Multi-Student Session",
            scheduled_at=now,
            status=SessionStatus.SCHEDULED,
            participants=[
                SessionParticipant(
                    student_id="student-other",
                    attempt_id="attempt-other",
                    joined_at=now,
                    connection_status="CONNECTED",
                ),
                SessionParticipant(
                    student_id=student_id,
                    attempt_id="attempt-mine",
                    joined_at=now,
                    connection_status="DISCONNECTED",
                ),
                SessionParticipant(
                    student_id="student-another",
                    connection_status="DISCONNECTED",
                ),
            ],
            created_by="teacher-789",
            created_at=now,
        )

        mock_session_repo.get_by_student.return_value = [session]

        query = GetMySessionsQuery(student_id=student_id)

        # Execute
        response = await use_case.execute(query)

        # Assert - should only include the requesting student's data
        assert len(response.sessions) == 1
        my_session = response.sessions[0]
        assert my_session.my_attempt_id == "attempt-mine"
        assert my_session.my_connection_status == "DISCONNECTED"
        # Should not include other students' info

    @pytest.mark.asyncio
    async def test_get_my_sessions_different_statuses(
        self, use_case, mock_session_repo
    ):
        """Test retrieving sessions with various statuses."""
        # Setup
        now = datetime.utcnow()
        student_id = "student-123"

        sessions = [
            Session(
                id="session-scheduled",
                class_id="class-001",
                test_id="test-001",
                title="Scheduled",
                scheduled_at=now,
                status=SessionStatus.SCHEDULED,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        connection_status="DISCONNECTED",
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
            Session(
                id="session-waiting",
                class_id="class-001",
                test_id="test-002",
                title="Waiting",
                scheduled_at=now,
                status=SessionStatus.WAITING_FOR_STUDENTS,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        connection_status="CONNECTED",
                        joined_at=now,
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
            Session(
                id="session-progress",
                class_id="class-001",
                test_id="test-003",
                title="In Progress",
                scheduled_at=now,
                started_at=now,
                status=SessionStatus.IN_PROGRESS,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        attempt_id="attempt-123",
                        connection_status="CONNECTED",
                        joined_at=now,
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
            Session(
                id="session-completed",
                class_id="class-001",
                test_id="test-004",
                title="Completed",
                scheduled_at=now,
                started_at=now,
                completed_at=now,
                status=SessionStatus.COMPLETED,
                participants=[
                    SessionParticipant(
                        student_id=student_id,
                        attempt_id="attempt-456",
                        connection_status="DISCONNECTED",
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
        ]

        mock_session_repo.get_by_student.return_value = sessions

        query = GetMySessionsQuery(student_id=student_id)

        # Execute
        response = await use_case.execute(query)

        # Assert
        assert len(response.sessions) == 4
        statuses = [s.status for s in response.sessions]
        assert SessionStatus.SCHEDULED in statuses
        assert SessionStatus.WAITING_FOR_STUDENTS in statuses
        assert SessionStatus.IN_PROGRESS in statuses
        assert SessionStatus.COMPLETED in statuses
