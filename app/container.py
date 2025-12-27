from dependency_injector import containers, providers

from app.application.services.passage_service import PassageService
from app.common.db.engine import get_database_session
from app.common.settings import settings
from app.infrastructure.repositories.sql_passage_repository import SQLPassageRepository
from app.infrastructure.repositories.sql_refresh_token_repository import (
    SQLRefreshTokenRepository,
)
from app.infrastructure.repositories.sql_user_repository import SqlUserRepository
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher_service import PasswordHasher
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.controllers.passage_controller import PassageController
from app.use_cases.auth.get_current_user.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from app.use_cases.auth.login.login_use_case import LoginUseCase
from app.use_cases.auth.register.register_use_case import RegisterUseCase
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
    config.from_env("jwt_algorithm", "JWT_ALGORITHM")
    config.from_env(
        "jwt_access_token_expire_minutes", "JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    database_session = providers.Resource(get_database_session)

    # Repositories (session will be provided at runtime)
    passage_repository = providers.Factory(
        SQLPassageRepository, session=database_session
    )
    user_repository = providers.Factory(SqlUserRepository, session=database_session)
    refresh_token_repository = providers.Factory(
        SQLRefreshTokenRepository, session=database_session
    )

    # Services
    passage_service = providers.Factory(PassageService, passage_repo=passage_repository)
    jwt_service = providers.Factory(
        JwtService, settings=settings, refresh_token_repo=refresh_token_repository
    )
    password_hasher = providers.Singleton(PasswordHasher)

    # Use Cases
    # Auth use cases
    login_use_case = providers.Factory(
        LoginUseCase,
        user_repo=user_repository,
        jwt_service=jwt_service,
        password_hasher=password_hasher,
    )

    register_use_case = providers.Factory(
        RegisterUseCase,
        user_repo=user_repository,
        token_service=jwt_service,
        password_hasher=password_hasher,
    )

    get_me_use_case = providers.Factory(
        GetCurrentUserUseCase, token_service=jwt_service
    )

    # Passage use cases
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
    auth_controller = providers.Factory(
        AuthController,
        login_use_case=login_use_case,
        register_use_case=register_use_case,
        get_me_use_case=get_me_use_case,
    )


# Global container instance
container = ApplicationContainer()
