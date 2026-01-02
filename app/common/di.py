"""Dependency injection helper functions."""

import inspect
from typing import get_type_hints

from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.db.engine import get_database_session
from app.container import container


def make_service_dependency(provider_dependency):
    """Create a FastAPI dependency that resolves a DI provider with request-scoped session.

    This function creates a FastAPI dependency that:
    1. Gets a database session for the request
    2. Resolves repositories with the session injected
    3. Resolves the requested service with all nested dependencies properly injected

    Usage:
        from dependency_injector.wiring import Provide
        from app.container import ApplicationContainer

        get_controller = make_service_dependency(
            Provide[ApplicationContainer.some_controller]
        )

        @router.get("/endpoint")
        async def handler(controller: SomeController = Depends(get_controller)):
            ...
    """

    @inject
    async def _dependency(
        session: AsyncSession = Depends(get_database_session),
        service_factory=Depends(provider_dependency),
    ):
        """
        Dependency function that:
        - Gets session from FastAPI's dependency injection
        - Resolves repositories with session injected
        - Resolves the service with all nested dependencies properly injected
        """
        # If service_factory is not callable, it's already resolved
        if not callable(service_factory):
            return service_factory

        # Inspect the factory to see what dependencies it needs
        sig = inspect.signature(service_factory)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            # Check if this parameter is a repository that needs a session
            if any(keyword in param_name.lower() for keyword in ["repository", "repo"]):
                # Get the repository provider from container
                repo_provider = getattr(container, param_name, None)
                if repo_provider and callable(repo_provider):
                    # Create repository instance with session
                    kwargs[param_name] = repo_provider(session=session)
            # Check if parameter has a default that's a provider
            elif hasattr(param.default, "__self__"):
                # It's a bound provider, call it to get the instance
                provider = param.default
                if callable(provider):
                    # Check if the provider's factory needs repositories
                    try:
                        sub_instance = _resolve_provider_with_repos(provider, session)
                        kwargs[param_name] = sub_instance
                    except:
                        # Fallback: just call the provider
                        kwargs[param_name] = provider()

        # Call the service factory with resolved dependencies
        if kwargs:
            return service_factory(**kwargs)
        else:
            return service_factory()

    def _resolve_provider_with_repos(provider, session):
        """Recursively resolve a provider, injecting session into repositories."""
        if not callable(provider):
            return provider

        sig = inspect.signature(provider)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if any(keyword in param_name.lower() for keyword in ["repository", "repo"]):
                # Get the repository provider from container
                repo_provider = getattr(container, param_name, None)
                if repo_provider and callable(repo_provider):
                    kwargs[param_name] = repo_provider(session=session)

        if kwargs:
            return provider(**kwargs)
        else:
            return provider()

    return _dependency
