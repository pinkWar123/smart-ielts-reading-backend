"""Integration tests for attempt endpoints."""

from datetime import datetime

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

    test_settings = Settings()
    test_settings.jwt_secret = "test-secret-key"
    test_settings.jwt_algorithm = "HS256"
    test_settings.jwt_access_token_expire_minutes = 30

    refresh_token_repo = MagicMock()
    return JwtService(settings=test_settings, refresh_token_repo=refresh_token_repo)


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
async def in_progress_attempt(test_db_session, student_user, test_entity):
    """Create an in-progress attempt in database."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    attempt = Attempt(
        test_id=test_entity.id,
        student_id=student_user.id,
        status=AttemptStatus.IN_PROGRESS,
        answers=[],
        highlighted_text=[],
        current_passage_index=0,
        current_question_index=0,
    )

    created_attempt = await attempt_repo.create(attempt)
    await test_db_session.commit()

    return created_attempt


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


# ============================================================================
# Update Progress Tests
# ============================================================================


@pytest.mark.asyncio
async def test_update_progress_success(test_client, student_token, in_progress_attempt):
    """Test successfully updating progress."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={
            "passage_index": 2,
            "question_index": 5,
            "passage_id": "passage_1",
            "question_id": "question_1",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["passage_index"] == 2
    assert data["question_index"] == 5
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_update_progress_without_optional_ids(
    test_client, student_token, in_progress_attempt
):
    """Test updating progress without passage_id and question_id."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={
            "passage_index": 1,
            "question_index": 3,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["passage_index"] == 1
    assert data["question_index"] == 3


@pytest.mark.asyncio
async def test_update_progress_fails_without_auth(test_client, in_progress_attempt):
    """Test updating progress fails without authentication."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={
            "passage_index": 1,
            "question_index": 0,
        },
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_update_progress_fails_as_teacher(
    test_client, teacher_token, in_progress_attempt
):
    """Test updating progress fails when user is not a student."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={
            "passage_index": 1,
            "question_index": 0,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_update_progress_fails_for_non_existent_attempt(
    test_client, student_token
):
    """Test updating progress fails for non-existent attempt."""
    response = await test_client.post(
        "/api/v1/attempts/non-existent-id/progress",
        json={
            "passage_index": 0,
            "question_index": 0,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 404  # Not found


@pytest.mark.asyncio
async def test_update_progress_fails_for_other_students_attempt(
    test_client, test_db_session, password_hasher, jwt_service, in_progress_attempt
):
    """Test updating progress fails when student tries to update another student's attempt."""
    # Create another student
    from app.domain.aggregates.users.user import User
    from app.infrastructure.repositories.sql_user_repository import (
        SqlUserRepositoryInterface,
    )

    user_repo = SqlUserRepositoryInterface(test_db_session)

    other_student = User(
        username="other_student",
        email="other@test.com",
        password_hash=password_hasher.hash("password123"),
        full_name="Other Student",
        role=UserRole.STUDENT,
        created_at=datetime.utcnow(),
    )

    created_other = await user_repo.create(other_student)
    await test_db_session.commit()

    # Generate token for other student
    payload = {
        "user_id": created_other.id,
        "username": created_other.username,
        "email": created_other.email,
        "role": created_other.role.value,
        "full_name": created_other.full_name,
    }
    other_token = jwt_service.encode(payload)

    # Try to update first student's attempt
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={
            "passage_index": 1,
            "question_index": 0,
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_update_progress_fails_for_submitted_attempt(
    test_client, student_token, test_db_session, student_user, test_entity
):
    """Test updating progress fails for submitted attempt."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Create submitted attempt
    submitted_attempt = Attempt(
        test_id=test_entity.id,
        student_id=student_user.id,
        status=AttemptStatus.SUBMITTED,  # Already submitted
        answers=[],
    )

    created = await attempt_repo.create(submitted_attempt)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/attempts/{created.id}/progress",
        json={
            "passage_index": 0,
            "question_index": 0,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 409  # Conflict (attempt already submitted)


@pytest.mark.asyncio
async def test_update_progress_multiple_times(
    test_client, student_token, in_progress_attempt
):
    """Test updating progress multiple times in sequence."""
    # First update
    response1 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={"passage_index": 0, "question_index": 5},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["passage_index"] == 0
    assert data1["question_index"] == 5

    # Second update
    response2 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={"passage_index": 1, "question_index": 0},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["passage_index"] == 1
    assert data2["question_index"] == 0

    # Third update
    response3 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={"passage_index": 1, "question_index": 10},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert response3.status_code == 200
    data3 = response3.json()
    assert data3["passage_index"] == 1
    assert data3["question_index"] == 10


# ============================================================================
# Record Highlight Tests
# ============================================================================


@pytest.mark.asyncio
async def test_record_highlight_success(
    test_client, student_token, in_progress_attempt
):
    """Test successfully recording a highlight."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "This is a highlighted text",
            "passage_id": "passage_1",
            "position_start": 10,
            "position_end": 35,
            "color": "yellow",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201  # Created
    data = response.json()

    assert data["text"] == "This is a highlighted text"
    assert data["passage_id"] == "passage_1"
    assert data["position_start"] == 10
    assert data["position_end"] == 35
    assert data["color"] == "yellow"
    assert "id" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_record_highlight_with_default_color(
    test_client, student_token, in_progress_attempt
):
    """Test recording highlight with default color."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Default color highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 23,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["color"] == "yellow"  # Default color


@pytest.mark.asyncio
async def test_record_highlight_with_different_colors(
    test_client, student_token, in_progress_attempt
):
    """Test recording highlights with different colors."""
    colors = ["yellow", "green", "blue", "red"]

    for color in colors:
        response = await test_client.post(
            f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
            json={
                "text": f"{color} highlight",
                "passage_id": "passage_1",
                "position_start": 0,
                "position_end": len(f"{color} highlight"),
                "color": color,
            },
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["color"] == color


@pytest.mark.asyncio
async def test_record_highlight_fails_without_auth(test_client, in_progress_attempt):
    """Test recording highlight fails without authentication."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Unauthorized highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 21,
        },
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_record_highlight_fails_as_teacher(
    test_client, teacher_token, in_progress_attempt
):
    """Test recording highlight fails when user is not a student."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Teacher highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 17,
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_record_highlight_fails_for_non_existent_attempt(
    test_client, student_token
):
    """Test recording highlight fails for non-existent attempt."""
    response = await test_client.post(
        "/api/v1/attempts/non-existent-id/highlights",
        json={
            "text": "Test highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 14,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 404  # Not found


@pytest.mark.asyncio
async def test_record_highlight_fails_with_invalid_position_range(
    test_client, student_token, in_progress_attempt
):
    """Test recording highlight fails when position_end <= position_start."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Invalid range",
            "passage_id": "passage_1",
            "position_start": 100,
            "position_end": 50,  # Invalid: end < start
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 400  # Bad Request (validation error)


@pytest.mark.asyncio
async def test_record_multiple_highlights(
    test_client, student_token, in_progress_attempt
):
    """Test recording multiple highlights in the same attempt."""
    highlights = [
        {
            "text": "First highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 15,
            "color": "yellow",
        },
        {
            "text": "Second highlight",
            "passage_id": "passage_1",
            "position_start": 20,
            "position_end": 36,
            "color": "green",
        },
        {
            "text": "Third highlight",
            "passage_id": "passage_2",
            "position_start": 0,
            "position_end": 15,
            "color": "blue",
        },
    ]

    highlight_ids = []

    for highlight in highlights:
        response = await test_client.post(
            f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
            json=highlight,
            headers={"Authorization": f"Bearer {student_token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["text"] == highlight["text"]
        assert data["passage_id"] == highlight["passage_id"]
        highlight_ids.append(data["id"])

    # Verify all highlights have unique IDs
    assert len(highlight_ids) == len(set(highlight_ids))


@pytest.mark.asyncio
async def test_record_highlight_fails_for_other_students_attempt(
    test_client, test_db_session, password_hasher, jwt_service, in_progress_attempt
):
    """Test recording highlight fails when student tries to update another student's attempt."""
    # Create another student
    from app.domain.aggregates.users.user import User
    from app.infrastructure.repositories.sql_user_repository import (
        SqlUserRepositoryInterface,
    )

    user_repo = SqlUserRepositoryInterface(test_db_session)

    other_student = User(
        username="other_student2",
        email="other2@test.com",
        password_hash=password_hasher.hash("password123"),
        full_name="Other Student 2",
        role=UserRole.STUDENT,
        created_at=datetime.utcnow(),
    )

    created_other = await user_repo.create(other_student)
    await test_db_session.commit()

    # Generate token for other student
    payload = {
        "user_id": created_other.id,
        "username": created_other.username,
        "email": created_other.email,
        "role": created_other.role.value,
        "full_name": created_other.full_name,
    }
    other_token = jwt_service.encode(payload)

    # Try to record highlight in first student's attempt
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Unauthorized highlight",
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 21,
        },
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_record_highlight_very_long_text(
    test_client, student_token, in_progress_attempt
):
    """Test recording highlight with very long text."""
    long_text = "A" * 5000  # Maximum allowed length

    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": long_text,
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 5000,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["text"]) == 5000


@pytest.mark.asyncio
async def test_record_highlight_text_too_long_fails(
    test_client, student_token, in_progress_attempt
):
    """Test recording highlight fails when text exceeds maximum length."""
    too_long_text = "A" * 5001  # Exceeds maximum

    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": too_long_text,
            "passage_id": "passage_1",
            "position_start": 0,
            "position_end": 5001,
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 400  # Bad Request (validation error)


# ============================================================================
# Combined Workflow Tests
# ============================================================================


@pytest.mark.asyncio
async def test_complete_attempt_workflow_with_progress_and_highlights(
    test_client, student_token, in_progress_attempt
):
    """Test complete workflow: update progress and record highlights together."""
    # Update progress to passage 0, question 0
    progress1 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={"passage_index": 0, "question_index": 0},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert progress1.status_code == 200

    # Highlight some text in passage 0
    highlight1 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Important passage 0 text",
            "passage_id": "passage_0",
            "position_start": 0,
            "position_end": 24,
            "color": "yellow",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert highlight1.status_code == 201

    # Move to next passage
    progress2 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/progress",
        json={"passage_index": 1, "question_index": 0},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert progress2.status_code == 200

    # Highlight text in passage 1
    highlight2 = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt.id}/highlights",
        json={
            "text": "Important passage 1 text",
            "passage_id": "passage_1",
            "position_start": 10,
            "position_end": 34,
            "color": "green",
        },
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert highlight2.status_code == 201

    # Verify final state by getting the attempt
    get_response = await test_client.get(
        f"/api/v1/attempts/{in_progress_attempt.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert get_response.status_code == 200
    attempt_data = get_response.json()

    # Verify progress
    assert attempt_data["current_passage_index"] == 1
    assert attempt_data["current_question_index"] == 0

    # Verify highlights
    assert len(attempt_data["highlighted_text"]) == 2
