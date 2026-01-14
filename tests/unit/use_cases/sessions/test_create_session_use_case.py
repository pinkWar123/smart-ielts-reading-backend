"""Unit tests for CreateSessionUseCase - Organized by class."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_cases.sessions.commands.create_session.create_session_dto import (
    CreateSessionRequest,
)
from app.application.use_cases.sessions.commands.create_session.create_session_use_case import (
    CreateSessionUseCase,
)
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.session import SessionStatus
from app.domain.aggregates.test import Test, TestStatus, TestType
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import NoPermissionToCreateSessionError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.errors.user_errors import UserNotFoundError


class TestCreateSessionUseCase:
    """Tests for CreateSessionUseCase - Click class arrow to run all tests."""

    @pytest.fixture
    def mock_session_repo(self):
        """Mock session repository."""
        repo = MagicMock()
        repo.create = AsyncMock()
        return repo

    @pytest.fixture
    def mock_class_repo(self):
        """Mock class repository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    @pytest.fixture
    def mock_test_repo(self):
        """Mock test repository."""
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
    def test_entity(self):
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
    def valid_request(self):
        """Create valid request fixture."""
        return CreateSessionRequest(
            class_id="class-001",
            test_id="test-001",
            title="Monday Morning Test",
            scheduled_at=datetime.utcnow() + timedelta(days=1),
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
        mock_session_repo.create.side_effect = lambda session: session

        response = await use_case.execute(valid_request, user_id=admin_user.id)

        assert response.class_id == valid_request.class_id
        assert response.test_id == valid_request.test_id
        assert response.title == valid_request.title
        assert response.status == SessionStatus.SCHEDULED
        assert len(response.participants) == 2
        assert response.created_by == admin_user.id

    @pytest.mark.asyncio
    async def test_create_session_success_as_teacher(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_test_repo,
        mock_session_repo,
        teacher_user,
        test_class,
        test_entity,
        valid_request,
    ):
        """Test successful session creation by teacher of the class."""
        mock_user_repo.get_by_id.return_value = teacher_user
        mock_class_repo.get_by_id.return_value = test_class
        mock_test_repo.get_by_id.return_value = test_entity
        mock_session_repo.create.side_effect = lambda session: session

        response = await use_case.execute(valid_request, user_id=teacher_user.id)

        assert response.status == SessionStatus.SCHEDULED
        assert response.created_by == teacher_user.id

    @pytest.mark.asyncio
    async def test_create_session_fails_user_not_found(
        self, use_case, mock_user_repo, valid_request
    ):
        """Test session creation fails when user doesn't exist."""
        mock_user_repo.get_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            await use_case.execute(valid_request, user_id="non-existent-user")

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

    @pytest.mark.asyncio
    async def test_create_session_fails_teacher_not_in_class(
        self, use_case, mock_user_repo, mock_class_repo, test_class, valid_request
    ):
        """Test session creation fails when teacher is not teaching the class."""
        other_teacher = User(
            id="other-teacher-999",
            username="otherteacher",
            email="other@test.com",
            password_hash="hashed",
            full_name="Other Teacher",
            role=UserRole.TEACHER,
            created_at=datetime.utcnow(),
        )

        mock_user_repo.get_by_id.return_value = other_teacher
        mock_class_repo.get_by_id.return_value = test_class

        with pytest.raises(NoPermissionToCreateSessionError):
            await use_case.execute(valid_request, user_id=other_teacher.id)

    @pytest.mark.asyncio
    async def test_create_session_fails_test_not_found(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_test_repo,
        teacher_user,
        test_class,
        valid_request,
    ):
        """Test session creation fails when test doesn't exist."""
        mock_user_repo.get_by_id.return_value = teacher_user
        mock_class_repo.get_by_id.return_value = test_class
        mock_test_repo.get_by_id.return_value = None

        with pytest.raises(TestNotFoundError):
            await use_case.execute(valid_request, user_id=teacher_user.id)

    @pytest.mark.asyncio
    async def test_create_session_initializes_participants(
        self,
        use_case,
        mock_user_repo,
        mock_class_repo,
        mock_test_repo,
        mock_session_repo,
        admin_user,
        test_entity,
        valid_request,
    ):
        """Test session creation initializes participants from class roster."""
        test_class = Class(
            id="class-001",
            name="Beacon 31",
            description="IELTS class",
            teacher_ids=["teacher-456"],
            student_ids=["student-1", "student-2", "student-3"],
            status=ClassStatus.ACTIVE,
            created_at=datetime.utcnow(),
            created_by="teacher-456",
        )

        mock_user_repo.get_by_id.return_value = admin_user
        mock_class_repo.get_by_id.return_value = test_class
        mock_test_repo.get_by_id.return_value = test_entity
        mock_session_repo.create.side_effect = lambda session: session

        response = await use_case.execute(valid_request, user_id=admin_user.id)

        assert len(response.participants) == 3
        participant_ids = [p.student_id for p in response.participants]
        assert "student-1" in participant_ids
        assert "student-2" in participant_ids
        assert "student-3" in participant_ids

        for participant in response.participants:
            assert participant.connection_status == "DISCONNECTED"
            assert participant.attempt_id is None
            assert participant.joined_at is None
