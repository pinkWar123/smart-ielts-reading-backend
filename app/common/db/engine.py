"""Database engine configuration for local environments."""

import os
from collections.abc import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

load_dotenv()


class DatabaseSettings:
    def __init__(self):
        # Check if we have a DATABASE_URL first (for backward compatibility)
        database_url = os.getenv("DATABASE_URL")
        if database_url and database_url.startswith("sqlite"):
            # Convert SQLite URL to async
            self.DATABASE_URL = database_url.replace(
                "sqlite:///", "sqlite+aiosqlite:///"
            )
        elif database_url and database_url.startswith("postgresql"):
            # Convert PostgreSQL URL to async
            self.DATABASE_URL = database_url.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        else:
            # Use individual settings for PostgreSQL
            self.DB_USER = os.getenv("DB_USER", "username")
            self.DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
            self.DB_HOST = os.getenv("DB_HOST", "localhost")
            self.DB_PORT = os.getenv("DB_PORT", "5432")
            self.DB_NAME = os.getenv("DB_NAME", "ielts_platform")
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

        self.DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
        self.DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        self.DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))
        self.DB_ECHO_SQL = os.getenv("DB_ECHO_SQL", "false").lower() == "true"


settings = DatabaseSettings()


async def get_database_engine():
    """Create async SQLAlchemy engine based on DATABASE_URL."""

    # Configure engine parameters based on database type
    if "sqlite" in settings.DATABASE_URL:
        # SQLite-specific configuration
        engine_kwargs = {
            "echo": settings.DB_ECHO_SQL,
            "connect_args": {"check_same_thread": False},
        }
    else:
        # PostgreSQL-specific configuration
        engine_kwargs = {
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "echo": settings.DB_ECHO_SQL,
        }

    engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)
    return engine


# Global engine instance
_engine = None
_session_factory = None


async def initialize_database():
    """Initialize the global database engine and session factory."""
    global _engine, _session_factory

    if _engine is None:
        _engine = await get_database_engine()
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the session factory, initializing it if necessary."""
    if _session_factory is None:
        await initialize_database()
    return _session_factory


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session with transaction control."""
    if _session_factory is None:
        await initialize_database()

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database():
    """Close the database engine and clean up resources."""
    global _engine, _session_factory

    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None


# Base class for SQLAlchemy models
Base = declarative_base()
