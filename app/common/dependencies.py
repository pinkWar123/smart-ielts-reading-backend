"""FastAPI dependencies for request-scoped service injection."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_use_case import (
    ExtractTestFromImagesUseCase,
)
from app.common.db.engine import get_database_session
from app.container import container
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.controllers.ocr_controller import OcrController
from app.presentation.controllers.passage_controller import PassageController
from app.presentation.controllers.test_controller import TestController


# Test-related dependencies
async def get_test_controller(
    session: AsyncSession = Depends(get_database_session),
) -> TestController:
    """Get TestController with session-scoped repositories and query services."""
    # Create repositories with session
    test_repo = container.test_repository(session=session)
    passage_repo = container.passage_repository(session=session)

    # Create query services with session
    test_query_service = container.test_query_service(session=session)

    # Create use cases with repositories and query services
    create_test_use_case = container.create_test_use_case(test_repository=test_repo)
    add_passage_use_case = container.add_passage_to_test_use_case(
        test_repository=test_repo, passage_repository=passage_repo
    )
    get_all_tests_use_case = container.get_all_tests_use_case(
        test_query_service=test_query_service
    )

    # Create and return controller
    return TestController(
        create_test_use_case=create_test_use_case,
        add_passage_to_test_use_case=add_passage_use_case,
        get_all_tests_use_case=get_all_tests_use_case,
    )


# Passage-related dependencies
async def get_passage_controller(
    session: AsyncSession = Depends(get_database_session),
) -> PassageController:
    """Get PassageController with session-scoped repositories."""
    # Create repository with session
    passage_repo = container.passage_repository(session=session)

    # Create use cases and services
    passage_service = container.passage_service(passage_repo=passage_repo)
    create_complete_passage_use_case = container.create_complete_passage_use_case(
        passage_repository=passage_repo
    )

    # Create and return controller
    return PassageController(
        passage_service=passage_service,
        create_complete_passage_use_case=create_complete_passage_use_case,
    )


# Auth-related dependencies
async def get_auth_controller(
    session: AsyncSession = Depends(get_database_session),
) -> AuthController:
    """Get AuthController with session-scoped repositories."""
    # Create repositories with session
    user_repo = container.user_repository(session=session)
    refresh_token_repo = container.refresh_token_repository(session=session)

    # Create services
    jwt_service = container.jwt_service(refresh_token_repo=refresh_token_repo)
    password_hasher = container.password_hasher()

    # Create use cases
    login_use_case = container.login_use_case(
        user_repo=user_repo, jwt_service=jwt_service, password_hasher=password_hasher
    )
    register_use_case = container.register_use_case(
        user_repo=user_repo, token_service=jwt_service, password_hasher=password_hasher
    )
    get_me_use_case = container.get_me_use_case(token_service=jwt_service)
    regenerate_tokens_use_case = container.regenerate_tokens_use_case(
        token_service=jwt_service, refresh_token_repo=refresh_token_repo
    )

    # Create and return controller
    return AuthController(
        login_use_case=login_use_case,
        register_use_case=register_use_case,
        get_me_use_case=get_me_use_case,
        regenerate_tokens_use_case=regenerate_tokens_use_case,
    )


# OCR-related dependencies (no database session needed)
async def get_ocr_controller() -> OcrController:
    """Get OcrController (no database dependencies)."""
    extract_text_use_case = container.extract_text_use_case()
    return OcrController(extract_text_use_case=extract_text_use_case)


async def get_extract_test_from_images_use_case() -> ExtractTestFromImagesUseCase:
    """Get ExtractTestFromImagesUseCase (no database dependencies)."""
    return container.extract_test_from_images_use_case()


async def get_jwt_service(
    session: AsyncSession = Depends(get_database_session),
):
    """Get JwtService with session-scoped refresh token repository."""
    refresh_token_repo = container.refresh_token_repository(session=session)
    return container.jwt_service(refresh_token_repo=refresh_token_repo)
