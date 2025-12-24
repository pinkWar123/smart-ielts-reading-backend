from dependency_injector import containers, providers

from app.application.services.passage_service import PassageService
from app.common.db.engine import get_database_session
from app.common.settings import settings
from app.infrastructure.repositories.sql_passage_repository import SQLPassageRepository
from app.infrastructure.security.jwt_service import JwtService
from app.presentation.controllers.passage_controller import PassageController
from app.use_cases.passages.create_passage.create_passage_use_case import (
    CreatePassageUseCase,
)
from app.use_cases.passages.get_passages.get_passages_use_case import GetPassagesUseCase


class ApplicationContainer(containers.DeclarativeContainer):
    """Main application container for dependency injection."""

    # Configuration
    config = providers.Configuration()
    config.from_env("jwt_secret", "JWT_SECRET")
    config.from_env("db_url", "DATABASE_URL")

    database_session = providers.Resource(get_database_session)

    # Repositories (session will be provided at runtime)
    passage_repository = providers.Factory(
        SQLPassageRepository, session=database_session
    )

    # Services
    passage_service = providers.Factory(PassageService, passage_repo=passage_repository)
    jwt_service = providers.Factory(JwtService,settings=settings)

    # Use Cases
    create_passage_use_case = providers.Factory(
        CreatePassageUseCase, passage_repo=passage_repository
    )

    get_passages_use_case = providers.Factory(
        GetPassagesUseCase, passage_repo=passage_repository
    )

    # Controllers
    passage_controller = providers.Factory(
        PassageController, passage_service=passage_service
    )


# Global container instance
container = ApplicationContainer()
