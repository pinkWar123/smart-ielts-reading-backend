"""Integration tests for submit attempt endpoint."""

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
async def test_with_passages(test_db_session, teacher_user):
    """Create test with passages and questions."""
    from app.domain.aggregates.passage.question import Question
    from app.domain.aggregates.passage.question_type import QuestionType
    from app.domain.aggregates.test import Test, TestStatus, TestType
    from app.domain.value_objects.question_value_objects import CorrectAnswer, Option
    from app.infrastructure.repositories.sql_test_repository import SQLTestRepository

    test_repo = SQLTestRepository(test_db_session)

    # Create test entity
    test = Test(
        title="IELTS Reading Test",
        test_type=TestType.FULL_TEST,
        status=TestStatus.PUBLISHED,
        time_limit_minutes=60,
        total_questions=3,
        total_points=3,
        created_at=datetime.utcnow(),
        created_by=teacher_user.id,
    )

    created_test = await test_repo.create(test)
    await test_db_session.commit()

    # Add passage with questions
    from app.domain.aggregates.passage.passage import Passage

    questions = [
        Question(
            question_number=1,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What is the main idea?",
            options=[
                Option(label="A", text="Option A"),
                Option(label="B", text="Option B"),
                Option(label="C", text="Option C"),
                Option(label="D", text="Option D"),
            ],
            correct_answer=CorrectAnswer(value="A"),
            order_in_passage=1,
        ),
        Question(
            question_number=2,
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text="What does the author suggest?",
            options=[
                Option(label="A", text="Option A"),
                Option(label="B", text="Option B"),
                Option(label="C", text="Option C"),
                Option(label="D", text="Option D"),
            ],
            correct_answer=CorrectAnswer(value="C"),
            order_in_passage=2,
        ),
        Question(
            question_number=3,
            question_type=QuestionType.TRUE_FALSE_NOT_GIVEN,
            question_text="The passage mentions climate change.",
            correct_answer=CorrectAnswer(value="TRUE"),
            order_in_passage=3,
        ),
    ]

    passage = Passage(
        title="Test Passage",
        content="This is a sample passage for testing.",
        passage_number=1,
        questions=questions,
    )

    await test_repo.add_passage(created_test.id, passage)
    await test_db_session.commit()

    # Reload test with passages
    test_with_passages = await test_repo.get_by_id_with_passages(created_test.id)
    return test_with_passages


@pytest.fixture
async def in_progress_attempt_with_answers(
    test_db_session, student_user, test_with_passages
):
    """Create an in-progress attempt with some answers."""
    from app.domain.aggregates.attempt.attempt import Answer, Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Get question IDs from the test
    questions = [q for p in test_with_passages.passages for q in p.questions]

    # Student answers: q1=A (correct), q2=B (wrong, correct is C), q3=not answered
    answers = [
        Answer(
            question_id=questions[0].id,
            student_answer="A",
            is_correct=False,  # Will be calculated on submit
            answered_at=datetime.utcnow(),
        ),
        Answer(
            question_id=questions[1].id,
            student_answer="B",
            is_correct=False,
            answered_at=datetime.utcnow(),
        ),
    ]

    attempt = Attempt(
        test_id=test_with_passages.id,
        student_id=student_user.id,
        status=AttemptStatus.IN_PROGRESS,
        time_remaining_seconds=1800,  # 30 minutes remaining
        answers=answers,
        highlighted_text=[],
        current_passage_index=0,
        current_question_index=0,
    )

    created_attempt = await attempt_repo.create(attempt)
    await test_db_session.commit()

    return created_attempt


@pytest.fixture
async def in_progress_attempt_no_answers(
    test_db_session, student_user, test_with_passages
):
    """Create an in-progress attempt with no answers."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    attempt = Attempt(
        test_id=test_with_passages.id,
        student_id=student_user.id,
        status=AttemptStatus.IN_PROGRESS,
        time_remaining_seconds=3600,  # Full hour remaining
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
# Submit Attempt Tests - Happy Path
# ============================================================================


@pytest.mark.asyncio
async def test_submit_attempt_success_with_scoring(
    test_client, student_token, in_progress_attempt_with_answers
):
    """Test successfully submitting an attempt with scoring."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert data["attempt_id"] == in_progress_attempt_with_answers.id
    assert data["status"] == "SUBMITTED"
    assert "submitted_at" in data
    assert data["total_questions"] == 3
    assert data["answered_questions"] == 2

    # Verify scoring (1 correct out of 2 answers)
    assert data["score"] == 0.5  # Less than 15 correct = band 0.5
    assert "time_taken_seconds" in data

    # Verify answers are marked correctly
    assert len(data["answers"]) == 2
    assert data["answers"][0]["is_correct"] is True  # q1: A is correct
    assert data["answers"][1]["is_correct"] is False  # q2: B is wrong


@pytest.mark.asyncio
async def test_submit_attempt_auto_time_expired(
    test_client, student_token, in_progress_attempt_with_answers
):
    """Test auto-submit when time expires."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "AUTO_TIME_EXPIRED"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "SUBMITTED"
    assert data["attempt_id"] == in_progress_attempt_with_answers.id


@pytest.mark.asyncio
async def test_submit_attempt_teacher_forced(
    test_client, student_token, in_progress_attempt_with_answers
):
    """Test teacher-forced submit."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "TEACHER_FORCED"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "SUBMITTED"


@pytest.mark.asyncio
async def test_submit_attempt_with_no_answers(
    test_client, student_token, in_progress_attempt_no_answers
):
    """Test submitting an attempt with no answers."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_no_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["status"] == "SUBMITTED"
    assert data["answered_questions"] == 0
    assert data["total_questions"] == 3
    assert data["score"] == 0.5  # Minimum band score


@pytest.mark.asyncio
async def test_submit_attempt_persists_to_database(
    test_client, student_token, test_db_session, in_progress_attempt_with_answers
):
    """Test that submission properly persists to database."""
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Submit attempt
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201

    # Reload from database
    updated_attempt = await attempt_repo.get_by_id(in_progress_attempt_with_answers.id)

    assert updated_attempt is not None
    assert updated_attempt.status.value == "SUBMITTED"
    assert updated_attempt.submitted_at is not None
    assert updated_attempt.band_score == 0.5
    assert updated_attempt.total_correct_answers == 1
    assert updated_attempt.submit_type.value == "MANUAL"

    # Verify answers are marked
    assert updated_attempt.answers[0].is_correct is True
    assert updated_attempt.answers[1].is_correct is False


@pytest.mark.asyncio
async def test_submit_calculates_time_taken_correctly(
    test_client, student_token, in_progress_attempt_with_answers
):
    """Test that time_taken is calculated correctly."""
    # Test is 60 minutes, 30 minutes (1800s) remaining
    # Time taken should be 60*60 - 1800 = 1800 seconds
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    expected_time_taken = 60 * 60 - 1800  # 1800 seconds (30 minutes)
    assert data["time_taken_seconds"] == expected_time_taken


# ============================================================================
# Submit Attempt Tests - Error Cases
# ============================================================================


@pytest.mark.asyncio
async def test_submit_attempt_without_auth(
    test_client, in_progress_attempt_with_answers
):
    """Test submitting fails without authentication."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_submit_attempt_as_teacher(
    test_client, teacher_token, in_progress_attempt_with_answers
):
    """Test submitting fails when user is not a student."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {teacher_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_submit_nonexistent_attempt(test_client, student_token):
    """Test submitting a non-existent attempt."""
    response = await test_client.post(
        "/api/v1/attempts/non-existent-id/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 404  # Not found


@pytest.mark.asyncio
async def test_submit_other_students_attempt(
    test_client,
    test_db_session,
    password_hasher,
    jwt_service,
    in_progress_attempt_with_answers,
):
    """Test student cannot submit another student's attempt."""
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

    # Try to submit first student's attempt
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 403  # Forbidden


@pytest.mark.asyncio
async def test_submit_already_submitted_attempt(
    test_client, student_token, test_db_session, student_user, test_with_passages
):
    """Test cannot submit an already submitted attempt."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Create already submitted attempt
    submitted_attempt = Attempt(
        test_id=test_with_passages.id,
        student_id=student_user.id,
        status=AttemptStatus.SUBMITTED,
        submitted_at=datetime.utcnow(),
        time_remaining_seconds=0,
        answers=[],
    )

    created = await attempt_repo.create(submitted_attempt)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/attempts/{created.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_submit_abandoned_attempt(
    test_client, student_token, test_db_session, student_user, test_with_passages
):
    """Test cannot submit an abandoned attempt."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Create abandoned attempt
    abandoned_attempt = Attempt(
        test_id=test_with_passages.id,
        student_id=student_user.id,
        status=AttemptStatus.ABANDONED,
        time_remaining_seconds=0,
        answers=[],
    )

    created = await attempt_repo.create(abandoned_attempt)
    await test_db_session.commit()

    response = await test_client.post(
        f"/api/v1/attempts/{created.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 409  # Conflict


@pytest.mark.asyncio
async def test_submit_with_invalid_submit_type(
    test_client, student_token, in_progress_attempt_with_answers
):
    """Test submitting with invalid submit type."""
    response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "INVALID_TYPE"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 422  # Validation error


# ============================================================================
# Submit Attempt Tests - Complete Workflow
# ============================================================================


@pytest.mark.asyncio
async def test_complete_test_taking_workflow(
    test_client, student_token, test_db_session, student_user, test_with_passages
):
    """Test complete workflow: answer questions, then submit."""
    from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
    from app.infrastructure.repositories.sql_attempt_repository import (
        SQLAttemptRepository,
    )

    attempt_repo = SQLAttemptRepository(test_db_session)

    # Create new attempt
    attempt = Attempt(
        test_id=test_with_passages.id,
        student_id=student_user.id,
        status=AttemptStatus.IN_PROGRESS,
        time_remaining_seconds=3600,
        answers=[],
    )

    created_attempt = await attempt_repo.create(attempt)
    await test_db_session.commit()

    # Get questions
    questions = [q for p in test_with_passages.passages for q in p.questions]

    # Answer questions (assuming you have an answer endpoint)
    # For this test, we'll directly add answers
    from app.domain.aggregates.attempt.attempt import Answer

    answers = [
        Answer(
            question_id=questions[0].id,
            student_answer="A",  # Correct
            is_correct=False,
            answered_at=datetime.utcnow(),
        ),
        Answer(
            question_id=questions[1].id,
            student_answer="C",  # Correct
            is_correct=False,
            answered_at=datetime.utcnow(),
        ),
        Answer(
            question_id=questions[2].id,
            student_answer="TRUE",  # Correct
            is_correct=False,
            answered_at=datetime.utcnow(),
        ),
    ]

    created_attempt.answers = answers
    created_attempt.time_remaining_seconds = 1200  # Used 40 minutes
    await attempt_repo.update(created_attempt)
    await test_db_session.commit()

    # Submit attempt
    response = await test_client.post(
        f"/api/v1/attempts/{created_attempt.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert response.status_code == 201
    data = response.json()

    # All 3 answers correct, but still below band 1.0 threshold (need 15+)
    assert data["answered_questions"] == 3
    assert data["total_questions"] == 3
    assert data["score"] == 0.5
    assert all(answer["is_correct"] for answer in data["answers"])


@pytest.mark.asyncio
async def test_get_submitted_attempt_returns_scores(
    test_client, student_token, test_db_session, in_progress_attempt_with_answers
):
    """Test that getting a submitted attempt returns correct scores."""
    # Submit attempt
    submit_response = await test_client.post(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}/submit",
        json={"submit_type": "MANUAL"},
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert submit_response.status_code == 201

    # Get attempt
    get_response = await test_client.get(
        f"/api/v1/attempts/{in_progress_attempt_with_answers.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )

    assert get_response.status_code == 200
    data = get_response.json()

    assert data["status"] == "SUBMITTED"
    assert data["band_score"] == 0.5
    assert data["total_correct_answers"] == 1
    assert data["submitted_at"] is not None
