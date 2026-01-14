"""Unit tests for StartWaitingUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.commands.start_waiting.start_waiting_use_case import (
    StartWaitingUseCase,
)
from app.application.use_cases.sessions.commands.start_waiting.start_wating_dto import (
    StartWaitingPhaseRequest,
)
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import (
    NoPermissionToManageSessionError,
    SessionNotFoundError,
)
from app.domain.errors.user_errors import UserNotFoundError


class TestStartWaitingUseCase:
    """Tests for StartWaitingUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        repo.update = AsyncMock()
        return repo

    @pytest.fixture
    def mock_class_repo(self):
        """Mock class repository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    @pytest.fixture
    def mock_connection_manager(self):
        """Mock connection manager service."""
        manager = MagicMock()
        manager.broadcast_to_session = AsyncMock()
        return manager

    @pytest.fixture
    def use_case(
        self,
        mock_session_repo,
        mock_class_repo,
        mock_user_repo,
        mock_connection_manager,
    ):
        """Create use case with mocked dependencies."""
        return StartWaitingUseCase(
            session_repo=mock_session_repo,
            class_repo=mock_class_repo,
            user_repo=mock_user_repo,
            connection_manager=mock_connection_manager,
        )

    @pytest.fixture
    def admin_user(self):
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
    def teacher_user(self):
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
    def student_user(self):
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
    def test_class(self, teacher_user):
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
    def scheduled_session(self, test_class):
        """Create session in SCHEDULED status."""
        return Session(
            id="session-001",
            class_id=test_class.id,
            test_id="test-001",
            title="Monday Morning Test",
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
            ],
            created_by="teacher-456",
            created_at=datetime.utcnow(),
        )

    @pytest.fixture
    def valid_request(self, scheduled_session):
        """Create valid request fixture."""
        return StartWaitingPhaseRequest(session_id=scheduled_session.id)

    @pytest.mark.asyncio
    async def test_start_waiting_success_as_admin(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_session_repo,
        mock_connection_manager,
        admin_user,
        test_class,
        scheduled_session,
        valid_request,
    ):
        """Test successful waiting phase start by admin."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = admin_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session
        mock_class_repo.get_by_id.return_value = test_class

        # Mock update to return updated session
        def mock_update(session):
            session.status = SessionStatus.WAITING_FOR_STUDENTS
            return session

        mock_session_repo.update.side_effect = mock_update

        response = await use_case.execute(valid_request, user_id=admin_user.id)

        assert response.status == SessionStatus.WAITING_FOR_STUDENTS
        mock_connection_manager.broadcast_to_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_waiting_success_as_teacher(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_session_repo,
        mock_connection_manager,
        teacher_user,
        test_class,
        scheduled_session,
        valid_request,
    ):
        """Test successful waiting phase start by teacher of the class."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = teacher_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session
        mock_class_repo.get_by_id.return_value = test_class

        def mock_update(session):
            session.status = SessionStatus.WAITING_FOR_STUDENTS
            return session

        mock_session_repo.update.side_effect = mock_update

        response = await use_case.execute(valid_request, user_id=teacher_user.id)

        assert response.status == SessionStatus.WAITING_FOR_STUDENTS
        mock_connection_manager.broadcast_to_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_waiting_fails_user_not_found(
        self, use_case, mock_user_repo, valid_request
    ):
        """Test waiting phase start fails when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await use_case.execute(valid_request, user_id="non-existent-user")

    @pytest.mark.asyncio
    async def test_start_waiting_fails_session_not_found(
        self, use_case, mock_user_repo, mock_session_repo, admin_user, valid_request
    ):
        """Test waiting phase start fails when session doesn't exist."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = admin_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = None

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(valid_request, user_id=admin_user.id)

    @pytest.mark.asyncio
    async def test_start_waiting_fails_student_role(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        student_user,
        scheduled_session,
        valid_request,
    ):
        """Test waiting phase start fails when user is a student."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = student_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session

        with pytest.raises(NoPermissionToManageSessionError):
            await use_case.execute(valid_request, user_id=student_user.id)

    @pytest.mark.asyncio
    async def test_start_waiting_fails_teacher_not_in_class(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        mock_class_repo,
        scheduled_session,
    ):
        """Test waiting phase start fails when teacher is not teaching the class."""
        other_teacher = User(
            id="other-teacher-999",
            username="otherteacher",
            email="other@test.com",
            password_hash="hashed",
            full_name="Other Teacher",
            role=UserRole.TEACHER,
            created_at=datetime.utcnow(),
        )

        test_class = Class(
            id="class-001",
            name="Beacon 31",
            description="IELTS class",
            teacher_ids=["teacher-456"],  # Different teacher
            student_ids=["student-1"],
            status=ClassStatus.ACTIVE,
            created_at=datetime.utcnow(),
            created_by="teacher-456",
        )

        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = other_teacher
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session
        mock_class_repo.get_by_id.return_value = test_class

        with pytest.raises(NoPermissionToManageSessionError):
            await use_case.execute(
                StartWaitingPhaseRequest(session_id=scheduled_session.id),
                user_id=other_teacher.id,
            )

    @pytest.mark.asyncio
    async def test_start_waiting_fails_class_not_found(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        mock_class_repo,
        teacher_user,
        scheduled_session,
        valid_request,
    ):
        """Test waiting phase start fails when class doesn't exist."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = teacher_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session
        mock_class_repo.get_by_id.return_value = None

        with pytest.raises(ClassNotFoundError):
            await use_case.execute(valid_request, user_id=teacher_user.id)

    @pytest.mark.asyncio
    async def test_start_waiting_broadcasts_message(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        mock_connection_manager,
        admin_user,
        scheduled_session,
        valid_request,
    ):
        """Test that starting waiting phase broadcasts WebSocket message."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = admin_user
        mock_user_repo.get_by_id.return_value = mock_user_model

        mock_session_repo.get_by_id.return_value = scheduled_session

        def mock_update(session):
            session.status = SessionStatus.WAITING_FOR_STUDENTS
            return session

        mock_session_repo.update.side_effect = mock_update

        await use_case.execute(valid_request, user_id=admin_user.id)

        # Verify WebSocket broadcast was called
        mock_connection_manager.broadcast_to_session.assert_called_once()
        call_args = mock_connection_manager.broadcast_to_session.call_args
        assert call_args[1]["session_id"] == scheduled_session.id
        message = call_args[1]["message"]
        assert message["type"] == "waiting_room_opened"
        assert message["session_id"] == scheduled_session.id
