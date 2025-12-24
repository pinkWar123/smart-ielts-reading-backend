"""Dependency injection helper functions."""

import inspect
from collections.abc import Callable
from typing import TypeVar

from dependency_injector.wiring import inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.engine import get_database_session

T = TypeVar("T")


async def resolve_service(
    service_factory: Callable[..., T], session: AsyncSession | None = None
) -> T:
    """
    Unified helper to resolve DI service providers that may return awaitables.

    This eliminates the ugly `if hasattr(created, "__await__")` pattern
    by providing a consistent way to handle both sync and async providers.

    Args:
        service_factory: The DI provider factory function
        session: Optional database session to pass to the factory

    Returns:
        The resolved service instance

    Example:
        # Before (ugly):
        try:
            created = service_factory(session=session)
        except TypeError:
            created = service_factory()
        if hasattr(created, "__await__"):
            created = await created
        return created

        # After (clean):
        return await resolve_service(service_factory, session)
    """
    try:
        # Try to pass session first (most common case)
        created = service_factory(session=session) if session else service_factory()
    except TypeError:
        # Fallback if factory doesn't accept session parameter
        created = service_factory()

    # Handle both async and sync providers uniformly
    if inspect.isawaitable(created):
        return await created

    return created


def make_service_dependency(provider_dependency):
    """Create a FastAPI dependency that resolves a DI provider with request-scoped session.

    Usage:
        get_service = make_service_dependency(
            Provide[Application.feature_container.some_service.provider]
        )

        @router.get("/endpoint")
        async def handler(service: SomeService = Depends(get_service)):
            ...
    """

    @inject
    async def _dependency(
        session: AsyncSession = Depends(get_database_session),
        service_factory=Depends(provider_dependency),
    ):
        # Check if service_factory is already an instance (resolved by DI container)
        if not callable(service_factory):
            # Already resolved - return the instance directly
            return service_factory

        # If it's still a factory, resolve it
        try:
            sig = inspect.signature(service_factory)
            if "session" in sig.parameters:
                return service_factory(session=session)
            else:
                return service_factory()
        except Exception:
            return service_factory()

    return _dependency
