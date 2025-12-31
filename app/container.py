from anthropic import AsyncAnthropic
from dependency_injector import containers, providers

from app.application.services.passage_service import PassageService
from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_use_case import \
    ExtractTestFromImagesUseCase
from app.common.db.engine import get_database_session
from app.common.settings import settings
from app.infrastructure.llm.claude_test_generator_service import ClaudeTestGeneratorService
from app.infrastructure.ocr.claude_image_to_text_service import ClaudeImageToTextService
from app.infrastructure.repositories.sql_passage_repository import SQLPassageRepository
from app.infrastructure.repositories.sql_refresh_token_repository import (
    SQLRefreshTokenRepository,
)
from app.infrastructure.repositories.sql_user_repository import SqlUserRepository
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher_service import PasswordHasher
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.controllers.ocr_controller import OcrController
from app.presentation.controllers.passage_controller import PassageController
from app.application.use_cases.auth.get_current_user.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from app.application.use_cases.auth.login.login_use_case import LoginUseCase
from app.application.use_cases.auth.regenerate_tokens.regenerate_tokens_use_case import (
    RegenerateTokensUseCase,
)
from app.application.use_cases.auth.register.register_use_case import RegisterUseCase
from app.application.use_cases.images.extract_text_from_image.extract_text_from_image_use_case import (
    ExtractTextFromImageUseCase,
)
from app.application.use_cases.passages.create_passage.create_passage_use_case import (
    CreatePassageUseCase,
)
from app.application.use_cases.passages.get_passages.get_passages_use_case import GetPassagesUseCase


def create_anthropic_client():
    return AsyncAnthropic(api_key=settings.claude_api_key)


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

    claude_client = providers.Factory(create_anthropic_client)
    image_to_text_service = providers.Factory(
        ClaudeImageToTextService, settings=settings, client=claude_client
    )
    test_generator_service = providers.Factory(
        ClaudeTestGeneratorService, settings=settings, client=claude_client
    )

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

    regenerate_tokens_use_case = providers.Factory(
        RegenerateTokensUseCase,
        token_service=jwt_service,
        refresh_token_repo=refresh_token_repository,
    )

    # Passage use cases
    create_passage_use_case = providers.Factory(
        CreatePassageUseCase, passage_repo=passage_repository
    )

    get_passages_use_case = providers.Factory(
        GetPassagesUseCase, passage_repo=passage_repository
    )

    # OCR use cases
    extract_text_use_case = providers.Factory(
        ExtractTextFromImageUseCase, image_to_text_service=image_to_text_service
    )

    # Test use cases
    extract_test_from_images_use_case = providers.Factory(
        ExtractTestFromImagesUseCase,
        test_generator_service=test_generator_service
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
        regenerate_tokens_use_case=regenerate_tokens_use_case,
    )
    ocr_controller = providers.Factory(
        OcrController, extract_text_use_case=extract_text_use_case
    )


# Global container instance
container = ApplicationContainer()
