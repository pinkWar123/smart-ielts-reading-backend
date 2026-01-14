"""Unit tests for CompleteSessionUseCase."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.commands.complete_session.complete_session_dto import (
    CompleteSessionRequest,
)
from app.application.use_cases.sessions.commands.complete_session.complete_session_use_case import (
    CompleteSessionUseCase,
)
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.session_errors import (
    NoPermissionToManageSessionError,
    SessionNotFoundError,
)
from app.domain.errors.user_errors import UserNotFoundError


class TestCompleteSessionUseCase:
    """Tests for CompleteSessionUseCase - Click class arrow to run all tests."""

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
        return CompleteSessionUseCase(
            session_repo=mock_session_repo,
            user_repo=mock_user_repo,
            class_repo=mock_class_repo,
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
    def in_progress_session(self, test_class, teacher_user):
        """Create session in IN_PROGRESS status."""
        return Session(
            id="session-001",
            class_id=test_class.id,
            test_id="test-001",
            title="Monday Morning Test",
            scheduled_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            status=SessionStatus.IN_PROGRESS,
            participants=[
                SessionParticipant(
                    student_id="student-1",
                    connection_status="CONNECTED",
                ),
                SessionParticipant(
                    student_id="student-2",
                    connection_status="CONNECTED",
                ),
            ],
            created_by=teacher_user.id,
            created_at=datetime.utcnow(),
        )

    @pytest.fixture
    def valid_request(self, in_progress_session):
        """Create valid request fixture."""
        return CompleteSessionRequest(session_id=in_progress_session.id)

    @pytest.mark.asyncio
    async def test_complete_session_success_as_admin(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        admin_user,
        in_progress_session,
        valid_request,
    ):
        """Test successful session completion by admin."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = admin_user
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_session_repo.get_by_id.return_value = in_progress_session

        # Mock update to return updated session
        def mock_update(session):
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            return session

        mock_session_repo.update.side_effect = mock_update

        response = await use_case.execute(valid_request, user_id=admin_user.id)

        assert response.success is True
        assert response.session_id == in_progress_session.id
        assert response.completed_by == admin_user.id
        assert response.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_session_success_as_teacher(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        mock_class_repo,
        teacher_user,
        test_class,
        in_progress_session,
        valid_request,
    ):
        """Test successful session completion by teacher of the class."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = teacher_user
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_session_repo.get_by_id.return_value = in_progress_session
        mock_class_repo.get_by_id.return_value = test_class

        def mock_update(session):
            session.status = SessionStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.updated_at = datetime.utcnow()
            return session

        mock_session_repo.update.side_effect = mock_update

        response = await use_case.execute(valid_request, user_id=teacher_user.id)

        assert response.success is True
        assert response.session_id == in_progress_session.id
        assert response.completed_by == teacher_user.id

    @pytest.mark.asyncio
    async def test_complete_session_fails_user_not_found(
        self, use_case, mock_user_repo, valid_request
    ):
        """Test session completion fails when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await use_case.execute(valid_request, user_id="non-existent-user")

    @pytest.mark.asyncio
    async def test_complete_session_fails_session_not_found(
        self, use_case, mock_user_repo, mock_session_repo, admin_user, valid_request
    ):
        """Test session completion fails when session doesn't exist."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = admin_user
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_session_repo.get_by_id.return_value = None

        with pytest.raises(SessionNotFoundError):
            await use_case.execute(valid_request, user_id=admin_user.id)

    @pytest.mark.asyncio
    async def test_complete_session_fails_student_role(
        self,
        use_case,
        mock_user_repo,
        mock_session_repo,
        student_user,
        in_progress_session,
        valid_request,
    ):
        """Test session completion fails when user is a student."""
        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = student_user
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_session_repo.get_by_id.return_value = in_progress_session

        with pytest.raises(NoPermissionToManageSessionError):
            await use_case.execute(valid_request, user_id=student_user.id)

    @pytest.mark.asyncio
    async def test_complete_session_fails_teacher_not_in_class(
        self, use_case, mock_user_repo, mock_session_repo, mock_class_repo
    ):
        """Test session completion fails when teacher is not teaching the class."""
        other_teacher = User(
            id="other-teacher-999",
            username="otherteacher",
            email="other@test.com",
            password_hash="hashed",
            full_name="Other Teacher",
            role=UserRole.TEACHER,
            created_at=datetime.utcnow(),
        )

        # Session references a class
        session = Session(
            id="session-001",
            class_id="class-001",
            test_id="test-001",
            title="Monday Morning Test",
            scheduled_at=datetime.utcnow(),
            started_at=datetime.utcnow(),
            status=SessionStatus.IN_PROGRESS,
            participants=[],
            created_by="teacher-456",
            created_at=datetime.utcnow(),
        )

        # Class has different teacher
        test_class = Class(
            id="class-001",
            name="Test Class",
            description="Test",
            teacher_ids=["teacher-456"],  # Different teacher
            student_ids=[],
            status=ClassStatus.ACTIVE,
            created_at=datetime.utcnow(),
            created_by="teacher-456",
        )

        # Mock UserModel with to_domain method
        mock_user_model = MagicMock()
        mock_user_model.to_domain.return_value = other_teacher
        mock_user_repo.get_by_id.return_value = mock_user_model
        mock_session_repo.get_by_id.return_value = session
        mock_class_repo.get_by_id.return_value = test_class

        with pytest.raises(NoPermissionToManageSessionError):
            await use_case.execute(
                CompleteSessionRequest(session_id=session.id),
                user_id=other_teacher.id,
            )
