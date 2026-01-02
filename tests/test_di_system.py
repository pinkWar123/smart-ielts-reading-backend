"""Tests for dependency injection system."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.common.dependencies import (
    get_auth_controller,
    get_passage_controller,
    get_test_controller,
)
from app.container import container
from app.infrastructure.persistence.models.test_model import Base


@pytest.fixture(scope="function")
async def test_session():
    """Create a test database session."""
    # Create in-memory SQLite database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Yield session for test
    async with session_factory() as session:
        yield session

    # Cleanup
    await engine.dispose()


@pytest.mark.asyncio
async def test_test_controller_injection(test_session):
    """Test that TestController gets proper dependencies with session."""
    # Call the dependency function
    controller = await get_test_controller(session=test_session)

    # Verify controller is created
    assert controller is not None
    assert hasattr(controller, "create_test_use_case")
    assert hasattr(controller, "add_passage_to_test_use_case")

    # Verify use cases have repositories
    assert controller.create_test_use_case is not None
    assert controller.add_passage_to_test_use_case is not None


@pytest.mark.asyncio
async def test_passage_controller_injection(test_session):
    """Test that PassageController gets proper dependencies with session."""
    # Call the dependency function
    controller = await get_passage_controller(session=test_session)

    # Verify controller is created
    assert controller is not None
    assert hasattr(controller, "passage_service")
    assert hasattr(controller, "create_complete_passage_use_case")

    # Verify dependencies are not None
    assert controller.passage_service is not None
    assert controller.create_complete_passage_use_case is not None


@pytest.mark.asyncio
async def test_auth_controller_injection(test_session):
    """Test that AuthController gets proper dependencies with session."""
    # Call the dependency function
    controller = await get_auth_controller(session=test_session)

    # Verify controller is created
    assert controller is not None
    assert hasattr(controller, "login_use_case")
    assert hasattr(controller, "register_use_case")
    assert hasattr(controller, "get_me_use_case")
    assert hasattr(controller, "regenerate_tokens_use_case")

    # Verify all use cases are created
    assert controller.login_use_case is not None
    assert controller.register_use_case is not None
    assert controller.get_me_use_case is not None
    assert controller.regenerate_tokens_use_case is not None


@pytest.mark.asyncio
async def test_session_isolation():
    """Test that different requests get different sessions."""
    # Create two separate sessions
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session1:
        async with session_factory() as session2:
            # Get controllers with different sessions
            controller1 = await get_test_controller(session=session1)
            controller2 = await get_test_controller(session=session2)

            # Verify they are different instances
            assert controller1 is not controller2
            assert (
                controller1.create_test_use_case is not controller2.create_test_use_case
            )

    await engine.dispose()


@pytest.mark.asyncio
async def test_repository_gets_session(test_session):
    """Test that repositories receive the session correctly."""
    # Create repository directly from container
    repo = container.test_repository(session=test_session)

    # Verify repository has session
    assert repo is not None
    assert hasattr(repo, "session")
    assert repo.session is test_session


@pytest.mark.asyncio
async def test_multiple_repositories_share_session(test_session):
    """Test that multiple repositories created in same request share the same session."""
    # Create repositories like the dependency function does
    test_repo = container.test_repository(session=test_session)
    passage_repo = container.passage_repository(session=test_session)

    # Verify both repositories have the same session
    assert test_repo.session is test_session
    assert passage_repo.session is test_session
    assert test_repo.session is passage_repo.session
