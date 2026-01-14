"""Integration tests for session endpoints."""

from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domain.aggregates.users.user import UserRole
from app.infrastructure.persistence.models import Base
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher_service import PasswordHasher
from main import app


@pytest.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db_session(test_engine):
    """Create test database session."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session


@pytest.fixture
async def test_client(test_db_session, jwt_service):
    """Create test HTTP client."""
    # Override database dependency
    from app.common.db.engine import get_database_session
    from app.common.dependencies import get_jwt_service

    async def override_get_db():
        yield test_db_session

    async def override_get_jwt():
        return jwt_service

    app.dependency_overrides[get_database_session] = override_get_db
    app.dependency_overrides[get_jwt_service] = override_get_jwt

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def password_hasher():
    """Create password hasher."""
    return PasswordHasher()


@pytest.fixture
def jwt_service():
    """Create JWT service for testing."""
    from unittest.mock import MagicMock

    from app.common.settings import Settings

    # Create test settings
    test_settings = Settings()
    test_settings.jwt_secret = "test-secret-key"
    test_settings.jwt_algorithm = "HS256"
    test_settings.jwt_access_token_expire_minutes = 30

    refresh_token_repo = MagicMock()
    return JwtService(settings=test_settings, refresh_token_repo=refresh_token_repo)


@pytest.fixture
async def admin_user(test_db_session, password_hasher):
    """Create admin user in database."""
    from app.domain.aggregates.users.user import User
    from app.infrastructure.repositories.sql_user_repository import (
        SqlUserRepositoryInterface,
    )

    user_repo = SqlUserRepositoryInterface(test_db_session)

    admin = User(
        username="admin",
        email="admin@test.com",
        password_hash=password_hasher.hash("password123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        created_at=datetime.utcnow(),
    )

    created_admin = await user_repo.create(admin)
    await test_db_session.commit()

    return created_admin


@pytest.fixture
async def teacher_user(test_db_session, password_hasher):
    """Create teacher user in database."""
    from app.domain.aggregates.users.user import User
    from app.infrastructure.repositories.sql_user_repository import (
        SqlUserRepositoryInterface,
    )

    user_repo = SqlUserRepositoryInterface(test_db_session)

    teacher = User(
        username="teacher",
        email="teacher@test.com",
        password_hash=password_hasher.hash("password123"),
        full_name="Teacher User",
        role=UserRole.TEACHER,
        created_at=datetime.utcnow(),
    )

    created_teacher = await user_repo.create(teacher)
    await test_db_session.commit()

    return created_teacher


@pytest.fixture
async def student_user(test_db_session, password_hasher):
    """Create student user in database."""
    from app.domain.aggregates.users.user import User
    from app.infrastructure.repositories.sql_user_repository import (
        SqlUserRepositoryInterface,
    )

    user_repo = SqlUserRepositoryInterface(test_db_session)

    student = User(
        username="student",
        email="student@test.com",
        password_hash=password_hasher.hash("password123"),
        full_name="Student User",
        role=UserRole.STUDENT,
        created_at=datetime.utcnow(),
    )

    created_student = await user_repo.create(student)
    await test_db_session.commit()

    return created_student


@pytest.fixture
async def test_class(test_db_session, teacher_user, student_user):
    """Create test class in database."""
    from app.domain.aggregates.class_ import Class, ClassStatus
    from app.infrastructure.repositories.sql_class_repository import SQLClassRepository

    class_repo = SQLClassRepository(test_db_session)

    test_class = Class(
        name="Beacon 31",
        description="IELTS Test Class",
        teacher_ids=[teacher_user.id],
        student_ids=[student_user.id],
        status=ClassStatus.ACTIVE,
        created_at=datetime.utcnow(),
        created_by=teacher_user.id,
    )

    created_class = await class_repo.create(test_class)
    await test_db_session.commit()

    return created_class


@pytest.fixture
async def test_entity(test_db_session, teacher_user):
    """Create test entity in database."""
    from app.domain.aggregates.test import Test, TestStatus, TestType
    from app.infrastructure.repositories.sql_test_repository import SQLTestRepository

    test_repo = SQLTestRepository(test_db_session)

    test = Test(
        title="Reading Test 1",
        test_type=TestType.FULL_TEST,
        status=TestStatus.PUBLISHED,
        time_limit_minutes=60,
        total_questions=40,
        total_points=40,
        created_at=datetime.utcnow(),
        created_by=teacher_user.id,
    )

    created_test = await test_repo.create(test)
    await test_db_session.commit()

    return created_test


@pytest.fixture
def admin_token(jwt_service, admin_user):
    """Generate admin JWT token."""
    payload = {
        "user_id": admin_user.id,
        "username": admin_user.username,
        "email": admin_user.email,
        "role": admin_user.role.value,
        "full_name": admin_user.full_name,
    }
    return jwt_service.encode(payload)


@pytest.fixture
def teacher_token(jwt_service, teacher_user):
    """Generate teacher JWT token."""
    payload = {
        "user_id": teacher_user.id,
        "username": teacher_user.username,
        "email": teacher_user.email,
        "role": teacher_user.role.value,
        "full_name": teacher_user.full_name,
    }
    return jwt_service.encode(payload)


@pytest.fixture
def student_token(jwt_service, student_user):
    """Generate student JWT token."""
    payload = {
        "user_id": student_user.id,
        "username": student_user.username,
        "email": student_user.email,
        "role": student_user.role.value,
        "full_name": student_user.full_name,
    }
    return jwt_service.encode(payload)


@pytest.mark.asyncio
async def test_create_session_as_admin(
    test_client, admin_token, test_class, test_entity
):
    """Test creating session as admin."""
    scheduled_at = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = await test_client.post(
        "/api/v1/sessions",
        json={
            "class_id": test_class.id,
            "test_id": test_entity.id,
            "title": "Monday Morning Test",
            "scheduled_at": scheduled_at,
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["class_id"] == test_class.id
    assert data["test_id"] == test_entity.id
    assert data["title"] == "Monday Morning Test"
    assert data["status"] == "SCHEDULED"
    assert len(data["participants"]) == 1  # One student in class
    assert data["participants"][0]["connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_create_session_as_teacher(
    test_client, teacher_token, test_class, test_entity
):
    """Test creating session as teacher of the class."""
    scheduled_at = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = await test_client.post(
        "/api/v1/sessions",
        json={
            "class_id": test_class.id,
            "test_id": test_entity.id,
            "title": "Reading Practice",
            "scheduled_at": scheduled_at,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "SCHEDULED"
    assert data["title"] == "Reading Practice"


@pytest.mark.asyncio
async def test_create_session_fails_as_student(
    test_client, student_token, test_class, test_entity
):
    """Test creating session fails for student role."""
    scheduled_at = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = await test_client.post(
        "/api/v1/sessions",
        json={
            "class_id": test_class.id,
            "test_id": test_entity.id,
            "title": "Should Fail",
            "scheduled_at": scheduled_at,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_create_session_fails_without_auth(test_client, test_class, test_entity):
    """Test creating session fails without authentication."""
    scheduled_at = (datetime.utcnow() + timedelta(days=1)).isoformat()

    response = await test_client.post(
        "/api/v1/sessions",
        json={
            "class_id": test_class.id,
            "test_id": test_entity.id,
            "title": "Should Fail",
            "scheduled_at": scheduled_at,
        },
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_list_sessions_by_teacher(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test listing sessions filtered by teacher."""
    # Create a session first
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    await session_repo.create(session)
    await test_db_session.commit()

    # List sessions
    response = await test_client.get(
        f"/api/v1/sessions?teacher_id={teacher_user.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "sessions" in data
    assert len(data["sessions"]) >= 1
    assert data["sessions"][0]["created_by"] == teacher_user.id


@pytest.mark.asyncio
async def test_get_session_by_id(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test getting session by ID."""
    # Create a session first
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Detailed Session",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status=SessionStatus.SCHEDULED,
        participants=[
            SessionParticipant(
                student_id="student-123",
                connection_status="DISCONNECTED",
            ),
        ],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    # Get session by ID
    response = await test_client.get(
        f"/api/v1/sessions/{created_session.id}",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_session.id
    assert data["title"] == "Detailed Session"
    assert data["status"] == "SCHEDULED"
    assert len(data["participants"]) >= 1


@pytest.mark.asyncio
async def test_get_session_by_id_not_found(test_client, teacher_token):
    """Test getting non-existent session returns 404."""
    response = await test_client.get(
        "/api/v1/sessions/non-existent-id",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_my_sessions_as_student(
    test_client,
    student_token,
    test_class,
    test_entity,
    test_db_session,
    teacher_user,
    student_user,
):
    """Test student getting their own sessions."""
    # Create a session with the student as participant
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Student Session",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status=SessionStatus.SCHEDULED,
        participants=[
            SessionParticipant(
                student_id=student_user.id,
                connection_status="DISCONNECTED",
            ),
        ],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    await session_repo.create(session)
    await test_db_session.commit()

    # Get student's sessions
    response = await test_client.get(
        "/api/v1/sessions/my-sessions",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "sessions" in data
    assert len(data["sessions"]) >= 1
    my_session = data["sessions"][0]
    assert my_session["title"] == "Student Session"
    assert "my_connection_status" in my_session
    assert my_session["my_connection_status"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_get_my_sessions_fails_for_non_student(test_client, teacher_token):
    """Test /my-sessions endpoint fails for non-student role."""
    response = await test_client.get(
        "/api/v1/sessions/my-sessions",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_start_waiting_phase_as_admin(
    test_client, admin_token, test_class, test_entity, test_db_session, admin_user
):
    """Test starting waiting phase as admin."""
    # Create a scheduled session first
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.SCHEDULED,
        participants=[
            SessionParticipant(
                student_id="student-1",
                connection_status="DISCONNECTED",
            )
        ],
        created_by=admin_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    # Start waiting phase
    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start-waiting",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_session.id
    assert data["status"] == "WAITING_FOR_STUDENTS"


@pytest.mark.asyncio
async def test_start_waiting_phase_as_teacher(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test starting waiting phase as teacher of the class."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Teacher's Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start-waiting",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "WAITING_FOR_STUDENTS"


@pytest.mark.asyncio
async def test_start_waiting_phase_fails_as_student(
    test_client, student_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test starting waiting phase fails for student role."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start-waiting",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_start_waiting_phase_session_not_found(test_client, admin_token):
    """Test starting waiting phase fails for non-existent session."""
    response = await test_client.post(
        "/api/v1/sessions/non-existent-id/start-waiting",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_start_session_as_admin(
    test_client, admin_token, test_class, test_entity, test_db_session, admin_user
):
    """Test starting session as admin."""
    # Create a session in WAITING_FOR_STUDENTS status
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Waiting Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.WAITING_FOR_STUDENTS,
        participants=[
            SessionParticipant(
                student_id="student-1",
                connection_status="CONNECTED",
            )
        ],
        created_by=admin_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    # Start session
    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["id"] == created_session.id
    assert data["status"] == "IN_PROGRESS"
    assert data["started_at"] is not None


@pytest.mark.asyncio
async def test_start_session_as_teacher(
    test_client,
    teacher_token,
    test_class,
    test_entity,
    test_db_session,
    teacher_user,
    student_user,
):
    """Test starting session as teacher of the class."""
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Teacher's Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.WAITING_FOR_STUDENTS,
        participants=[
            SessionParticipant(
                student_id=student_user.id,
                connection_status="CONNECTED",
            )
        ],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"


@pytest.mark.asyncio
async def test_start_session_fails_as_student(
    test_client, student_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test starting session fails for student role."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.WAITING_FOR_STUDENTS,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/start",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_start_session_not_found(test_client, admin_token):
    """Test starting session fails for non-existent session."""
    response = await test_client.post(
        "/api/v1/sessions/non-existent-id/start",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_session_as_admin(
    test_client, admin_token, test_class, test_entity, test_db_session, admin_user
):
    """Test cancelling session as admin."""
    # Create a session in progress
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Active Session",
        scheduled_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=admin_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    # Cancel session
    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["session_id"] == created_session.id
    assert data["success"] is True
    assert data["cancelled_by"] == admin_user.id
    assert data["cancelled_at"] is not None


@pytest.mark.asyncio
async def test_cancel_session_as_teacher(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test cancelling session as teacher of the class."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Teacher's Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/cancel",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["cancelled_by"] == teacher_user.id


@pytest.mark.asyncio
async def test_cancel_session_fails_as_student(
    test_client, student_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test cancelling session fails for student role."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        status=SessionStatus.IN_PROGRESS,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/cancel",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_cancel_session_not_found(test_client, admin_token):
    """Test cancelling session fails for non-existent session."""
    response = await test_client.post(
        "/api/v1/sessions/non-existent-id/cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_scheduled_session(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test cancelling a scheduled session that hasn't started yet."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Future Session",
        scheduled_at=datetime.utcnow() + timedelta(days=1),
        status=SessionStatus.SCHEDULED,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/cancel",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_complete_session_as_admin(
    test_client, admin_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test completing an in-progress session as admin."""
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        status=SessionStatus.IN_PROGRESS,
        participants=[
            SessionParticipant(
                student_id="student-1",
                connection_status="CONNECTED",
            )
        ],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/complete",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["session_id"] == created_session.id
    assert data["completed_at"] is not None


@pytest.mark.asyncio
async def test_complete_session_as_teacher(
    test_client,
    teacher_token,
    test_class,
    test_entity,
    test_db_session,
    teacher_user,
    student_user,
):
    """Test completing an in-progress session as teacher of the class."""
    from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Teacher's Session",
        scheduled_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        status=SessionStatus.IN_PROGRESS,
        participants=[
            SessionParticipant(
                student_id=student_user.id,
                connection_status="CONNECTED",
            )
        ],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/complete",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_complete_session_fails_as_student(
    test_client, student_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test completing session fails for student role."""
    from app.domain.aggregates.session import Session, SessionStatus
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)

    session = Session(
        class_id=test_class.id,
        test_id=test_entity.id,
        title="Test Session",
        scheduled_at=datetime.utcnow(),
        started_at=datetime.utcnow(),
        status=SessionStatus.IN_PROGRESS,
        participants=[],
        created_by=teacher_user.id,
        created_at=datetime.utcnow(),
    )

    created_session = await session_repo.create(session)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/sessions/{created_session.id}/complete",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_complete_session_not_found(test_client, admin_token):
    """Test completing session fails for non-existent session."""
    response = await test_client.post(
        "/api/v1/sessions/non-existent-id/complete",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_full_session_workflow(
    test_client, teacher_token, test_class, test_entity, test_db_session, teacher_user
):
    """Test complete session workflow: create -> start waiting -> start -> complete."""
    # 1. Create session
    scheduled_at = (datetime.utcnow() + timedelta(days=1)).isoformat()

    create_response = await test_client.post(
        "/api/v1/sessions",
        json={
            "class_id": test_class.id,
            "test_id": test_entity.id,
            "title": "Full Workflow Test",
            "scheduled_at": scheduled_at,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert create_response.status_code == 200
    session_data = create_response.json()
    session_id = session_data["id"]
    assert session_data["status"] == "SCHEDULED"

    # 2. Start waiting phase
    waiting_response = await test_client.post(
        f"/api/v1/sessions/{session_id}/start-waiting",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert waiting_response.status_code == 200
    waiting_data = waiting_response.json()
    assert waiting_data["status"] == "WAITING_FOR_STUDENTS"

    # 2.5. Manually connect a student (simulating WebSocket join)
    from app.infrastructure.repositories.sql_session_repository import (
        SQLSessionRepository,
    )

    session_repo = SQLSessionRepository(test_db_session)
    session = await session_repo.get_by_id(session_id)

    # Simulate student joining the session
    if session and session.participants:
        session.participants[0].connection_status = "CONNECTED"
        await session_repo.update(session)
        await test_db_session.commit()

    # 3. Start session
    start_response = await test_client.post(
        f"/api/v1/sessions/{session_id}/start",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert start_response.status_code == 200
    start_data = start_response.json()
    assert start_data["status"] == "IN_PROGRESS"
    assert start_data["started_at"] is not None

    # 4. Complete session (test finished or manually stopped)
    complete_response = await test_client.post(
        f"/api/v1/sessions/{session_id}/complete",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["success"] is True
    assert complete_data["session_id"] == session_id
    assert complete_data["completed_at"] is not None
