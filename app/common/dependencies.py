"""FastAPI dependencies for request-scoped service injection."""

from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.application.use_cases.passages.create_complete_passage.create_complete_passage_use_case import (
    CreateCompletePassageUseCase,
)
from app.application.use_cases.passages.delete_passage_by_id.delete_passage_by_id_use_case import (
    DeletePassageByIdUseCase,
)
from app.application.use_cases.passages.get_all_passages.get_all_passages_use_case import (
    GetAllPassagesUseCase,
)
from app.application.use_cases.passages.get_test_detail.get_test_detail_use_case import (
    GetTestDetailUseCase,
)
from app.application.use_cases.passages.get_test_with_passages.get_test_with_passages_use_case import (
    GetTestWithPassagesUseCase,
)
from app.application.use_cases.tests.add_passage_to_test.add_passage_to_test_use_case import (
    AddPassageToTestUseCase,
)
from app.application.use_cases.tests.create_test.create_test_use_case import (
    CreateTestUseCase,
)
from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_use_case import (
    ExtractTestFromImagesUseCase,
)
from app.application.use_cases.tests.get_all_tests.get_all_tests_use_case import (
    GetAllTestsUseCase,
)
from app.common.db.engine import get_database_session
from app.container import container


@dataclass
class AuthUseCases:
    login: LoginUseCase
    register: RegisterUseCase
    get_me: GetCurrentUserUseCase
    regenerate_tokens: RegenerateTokensUseCase


@dataclass
class TestUseCases:
    get_test_by_id: GetTestWithPassagesUseCase
    get_test_detail_by_id: GetTestDetailUseCase
    create_test: CreateTestUseCase
    add_passage_to_test: AddPassageToTestUseCase
    get_all_tests: GetAllTestsUseCase
    remove_passage_use_case: DeletePassageByIdUseCase


@dataclass
class PassageUseCases:
    create_complete_passage: CreateCompletePassageUseCase
    get_all_passages: GetAllPassagesUseCase


@dataclass
class OcrUseCases:
    extract_text: ExtractTextFromImageUseCase
    extract_test: ExtractTestFromImagesUseCase


# Test-related dependencies
async def get_test_use_cases(
    session: AsyncSession = Depends(get_database_session),
) -> TestUseCases:
    """Get TestUseCases with session-scoped repositories and query services."""
    # Create repositories with session
    test_repo = container.test_repository(session=session)
    passage_repo = container.passage_repository(session=session)

    # Create query services with session
    test_query_service = container.test_query_service(session=session)

    # Create and return use cases
    return TestUseCases(
        create_test=container.create_test_use_case(test_repository=test_repo),
        add_passage_to_test=container.add_passage_to_test_use_case(
            test_repository=test_repo, passage_repository=passage_repo
        ),
        get_all_tests=container.get_all_tests_use_case(
            test_query_service=test_query_service
        ),
        remove_passage_use_case=container.remove_passage_use_case(
            test_query_service=test_query_service, test_repository=test_repo
        ),
        get_test_by_id=container.get_test_by_id(test_query_service=test_query_service),
        get_test_detail_by_id=container.get_test_detail_by_id(
            test_query_service=test_query_service
        ),
    )


# Passage-related dependencies
async def get_passage_use_cases(
    session: AsyncSession = Depends(get_database_session),
) -> PassageUseCases:
    """Get PassageUseCases with session-scoped repositories."""
    # Create repository with session
    passage_repo = container.passage_repository(session=session)

    # Create passage service
    passage_service = container.passage_service(passage_repo=passage_repo)

    # Create and return use cases
    return PassageUseCases(
        create_complete_passage=container.create_complete_passage_use_case(
            passage_repository=passage_repo
        ),
        get_all_passages=container.get_all_passages_use_case(
            passage_service=passage_service
        ),
    )


# Auth-related dependencies
async def get_auth_use_cases(
    session: AsyncSession = Depends(get_database_session),
) -> AuthUseCases:
    """Get AuthUseCases with session-scoped repositories."""
    # Create repositories with session
    user_repo = container.user_repository(session=session)
    refresh_token_repo = container.refresh_token_repository(session=session)

    # Create services
    jwt_service = container.jwt_service(refresh_token_repo=refresh_token_repo)
    password_hasher = container.password_hasher()

    # Create and return use cases
    return AuthUseCases(
        login=container.login_use_case(
            user_repo=user_repo,
            jwt_service=jwt_service,
            password_hasher=password_hasher,
        ),
        register=container.register_use_case(
            user_repo=user_repo,
            token_service=jwt_service,
            password_hasher=password_hasher,
        ),
        get_me=container.get_me_use_case(token_service=jwt_service),
        regenerate_tokens=container.regenerate_tokens_use_case(
            token_service=jwt_service, refresh_token_repo=refresh_token_repo
        ),
    )


# OCR-related dependencies (no database session needed)
async def get_ocr_use_cases() -> OcrUseCases:
    """Get OcrUseCases (no database dependencies)."""
    return OcrUseCases(
        extract_text=container.extract_text_use_case(),
        extract_test=container.extract_test_from_images_use_case(),
    )


async def get_jwt_service(
    session: AsyncSession = Depends(get_database_session),
):
    """Get JwtService with session-scoped refresh token repository."""
    refresh_token_repo = container.refresh_token_repository(session=session)
    return container.jwt_service(refresh_token_repo=refresh_token_repo)
