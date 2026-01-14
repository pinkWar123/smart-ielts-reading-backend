"""Organized unit tests for session use cases - Run all tests in this file together."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.commands.create_session.create_session_dto import (
    CreateSessionRequest,
)
from app.application.use_cases.sessions.commands.create_session.create_session_use_case import (
    CreateSessionUseCase,
)
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_dto import (
    GetMySessionsQuery,
)
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_use_case import (
    GetMySessionsUseCase,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_dto import (
    GetSessionByIdQuery,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_use_case import (
    GetSessionByIdUseCase,
)
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_dto import (
    ListSessionsQuery,
)
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_use_case import (
    ListSessionsUseCase,
)
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
from app.domain.aggregates.test import Test, TestStatus, TestType
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import (
    NoPermissionToCreateSessionError,
    SessionNotFoundError,
)
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.errors.user_errors import UserNotFoundError

# ============================================================================
# Shared Fixtures
# ============================================================================


@pytest.fixture
def mock_session_repo():
    """Mock session repository."""
    repo = MagicMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_teacher = AsyncMock()
    repo.get_by_class = AsyncMock()
    repo.get_by_student = AsyncMock()
    repo.get_active_sessions = AsyncMock()
    return repo


@pytest.fixture
def mock_class_repo():
    """Mock class repository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_test_repo():
    """Mock test repository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_user_repo():
    """Mock user repository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def admin_user():
    """Create admin user fixture."""
    return User(
        id="admin-123",
        username="admin",
        email="admin@test.com",
        password_hash="hashed",
        full_name="Admin User",
        role=UserRole.ADMIN,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def teacher_user():
    """Create teacher user fixture."""
    return User(
        id="teacher-456",
        username="teacher",
        email="teacher@test.com",
        password_hash="hashed",
        full_name="Teacher User",
        role=UserRole.TEACHER,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def student_user():
    """Create student user fixture."""
    return User(
        id="student-789",
        username="student",
        email="student@test.com",
        password_hash="hashed",
        full_name="Student User",
        role=UserRole.STUDENT,
        created_at=datetime.utcnow(),
    )


@pytest.fixture
def test_class(teacher_user):
    """Create class fixture."""
    return Class(
        id="class-001",
        name="Beacon 31",
        description="IELTS class",
        teacher_ids=[teacher_user.id],
        student_ids=["student-1", "student-2"],
        status=ClassStatus.ACTIVE,
        created_at=datetime.utcnow(),
        created_by=teacher_user.id,
    )


@pytest.fixture
def test_entity():
    """Create test fixture."""
    return Test(
        id="test-001",
        title="Reading Test 1",
        test_type=TestType.FULL_TEST,
        status=TestStatus.PUBLISHED,
        time_limit_minutes=60,
        total_questions=40,
        total_points=40,
        created_at=datetime.utcnow(),
        created_by="teacher-456",
    )


@pytest.fixture
def valid_request():
    """Create valid request fixture."""
    return CreateSessionRequest(
        class_id="class-001",
        test_id="test-001",
        title="Monday Morning Test",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
    )


# ============================================================================
# Test Classes - Click the green arrow next to class name to run all tests
# ============================================================================


class TestCreateSessionUseCase:
    """Tests for CreateSessionUseCase - Run all at once by clicking class-level arrow."""

    @pytest.fixture
    def use_case(
        self, mock_session_repo, mock_class_repo, mock_test_repo, mock_user_repo
    ):
        """Create use case with mocked dependencies."""
        return CreateSessionUseCase(
            session_repo=mock_session_repo,
            class_repo=mock_class_repo,
            test_repo=mock_test_repo,
            user_repo=mock_user_repo,
        )

    @pytest.mark.asyncio
    async def test_create_session_success_as_admin(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_test_repo,
        mock_session_repo,
        admin_user,
        test_class,
        test_entity,
        valid_request,
    ):
        """Test successful session creation by admin."""
        mock_user_repo.get_by_id.return_value = admin_user
        mock_class_repo.get_by_id.return_value = test_class
        mock_test_repo.get_by_id.return_value = test_entity

        def create_session_side_effect(session):
            return session

        mock_session_repo.create.side_effect = create_session_side_effect

        response = await use_case.execute(valid_request, user_id=admin_user.id)

        assert response.status == SessionStatus.SCHEDULED
        assert response.title == "Monday Morning Test"
        assert len(response.participants) == 2

    @pytest.mark.asyncio
    async def test_create_session_fails_student_role(
        self, use_case, mock_user_repo, student_user, valid_request
    ):
        """Test session creation fails when user is a student."""
        mock_user_repo.get_by_id.return_value = student_user

        with pytest.raises(NoPermissionToCreateSessionError):
            await use_case.execute(valid_request, user_id=student_user.id)

    @pytest.mark.asyncio
    async def test_create_session_fails_class_not_found(
        self, use_case, mock_user_repo, mock_class_repo, teacher_user, valid_request
    ):
        """Test session creation fails when class doesn't exist."""
        mock_user_repo.get_by_id.return_value = teacher_user
        mock_class_repo.get_by_id.return_value = None

        with pytest.raises(ClassNotFoundError):
            await use_case.execute(valid_request, user_id=teacher_user.id)


class TestListSessionsUseCase:
    """Tests for ListSessionsUseCase - Run all at once."""

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
        ]

    @pytest.mark.asyncio
    async def test_list_sessions_by_teacher(
        self, use_case, mock_session_repo, sample_sessions
    ):
        """Test listing sessions filtered by teacher."""
        mock_session_repo.get_by_teacher.return_value = sample_sessions

        query = ListSessionsQuery(teacher_id="teacher-123")
        response = await use_case.execute(query)

        assert len(response.sessions) == 2
        assert all(s.created_by == "teacher-123" for s in response.sessions)

    @pytest.mark.asyncio
    async def test_list_sessions_by_class(
        self, use_case, mock_session_repo, sample_sessions
    ):
        """Test listing sessions filtered by class."""
        mock_session_repo.get_by_class.return_value = sample_sessions

        query = ListSessionsQuery(class_id="class-001")
        response = await use_case.execute(query)

        assert len(response.sessions) == 2


class TestGetSessionByIdUseCase:
    """Tests for GetSessionByIdUseCase - Run all at once."""

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
                    connection_status="DISCONNECTED",
                ),
            ],
            created_by="teacher-789",
            created_at=now,
        )

    @pytest.mark.asyncio
    async def test_get_session_by_id_success(
        self, use_case, mock_session_repo, sample_session
    ):
        """Test successfully retrieving session by ID."""
        mock_session_repo.get_by_id.return_value = sample_session

        query = GetSessionByIdQuery(session_id="session-123")
        response = await use_case.execute(query)

        assert response.id == "session-123"
        assert response.title == "Monday Test"
        assert len(response.participants) == 1

    @pytest.mark.asyncio
    async def test_get_session_by_id_not_found(self, use_case, mock_session_repo):
        """Test error when session doesn't exist."""
        mock_session_repo.get_by_id.return_value = None

        query = GetSessionByIdQuery(session_id="non-existent")

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(query)


class TestGetMySessionsUseCase:
    """Tests for GetMySessionsUseCase - Run all at once."""

    @pytest.fixture
    def use_case(self, mock_session_repo):
        """Create use case with mocked dependencies."""
        return GetMySessionsUseCase(session_repo=mock_session_repo)

    @pytest.mark.asyncio
    async def test_get_my_sessions_success(self, use_case, mock_session_repo):
        """Test successfully retrieving student's sessions."""
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
                        connection_status="DISCONNECTED",
                    ),
                ],
                created_by="teacher-789",
                created_at=now,
            ),
        ]

        mock_session_repo.get_by_student.return_value = sessions

        query = GetMySessionsQuery(student_id=student_id)
        response = await use_case.execute(query)

        assert len(response.sessions) == 1
        assert response.sessions[0].my_connection_status == "DISCONNECTED"

    @pytest.mark.asyncio
    async def test_get_my_sessions_empty_result(self, use_case, mock_session_repo):
        """Test retrieving sessions when student has no sessions."""
        mock_session_repo.get_by_student.return_value = []

        query = GetMySessionsQuery(student_id="student-999")
        response = await use_case.execute(query)

        assert len(response.sessions) == 0
