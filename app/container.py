from anthropic import AsyncAnthropic
from dependency_injector import containers, providers

from app.application.services.passage_service import PassageService
from app.application.use_cases.auth.commands.login.login_use_case import LoginUseCase
from app.application.use_cases.auth.commands.regenerate_tokens.regenerate_tokens_use_case import (
    RegenerateTokensUseCase,
)
from app.application.use_cases.auth.commands.register.register_use_case import (
    RegisterUseCase,
)
from app.application.use_cases.auth.queries.get_current_user.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from app.application.use_cases.classes.commands.assign_teacher.assign_teacher_use_case import (
    AssignTeacherUseCase,
)
from app.application.use_cases.classes.commands.create_class.create_class_use_case import (
    CreateClassUseCase,
)
from app.application.use_cases.classes.commands.enroll_student.enroll_student_use_case import (
    EnrollStudentUseCase,
)
from app.application.use_cases.classes.commands.remove_student.remove_student_use_case import (
    RemoveStudentUseCase,
)
from app.application.use_cases.classes.commands.remove_teacher.remove_teacher_use_case import (
    RemoveTeacherUseCase,
)
from app.application.use_cases.classes.queries.get_class_by_id.get_class_by_id_use_case import (
    GetClassByIdUseCase,
)
from app.application.use_cases.classes.queries.list_classes.list_classes_use_case import (
    ListClassesUseCase,
)
from app.application.use_cases.images.queries.extract_text_from_image.extract_text_from_image_use_case import (
    ExtractTextFromImageUseCase,
)
from app.application.use_cases.passages.commands.create_complete_passage.create_complete_passage_use_case import (
    CreateCompletePassageUseCase,
)
from app.application.use_cases.passages.commands.create_passage.create_passage_use_case import (
    CreatePassageUseCase,
)
from app.application.use_cases.passages.commands.delete_passage_by_id.delete_passage_by_id_use_case import (
    DeletePassageByIdUseCase,
)
from app.application.use_cases.passages.commands.update_passage.update_passage_use_case import (
    UpdatePassageUseCase,
)
from app.application.use_cases.passages.queries.get_all_passages.get_all_passages_use_case import (
    GetAllPassagesUseCase,
)
from app.application.use_cases.passages.queries.get_passage_detail_by_id.get_passage_detail_use_case import (
    GetPassageDetailByIdUseCase,
)
from app.application.use_cases.passages.queries.get_passages.get_passages_use_case import (
    GetPassagesUseCase,
)
from app.application.use_cases.tests.commands.add_passage_to_test.add_passage_to_test_use_case import (
    AddPassageToTestUseCase,
)
from app.application.use_cases.tests.commands.create_test.create_test_use_case import (
    CreateTestUseCase,
)
from app.application.use_cases.tests.commands.publish_test.publish_test_use_case import (
    PublishTestUseCase,
)
from app.application.use_cases.tests.queries.extract_test.extract_test_from_images.extract_test_from_images_use_case import (
    ExtractTestFromImagesUseCase,
)
from app.application.use_cases.tests.queries.get_all_tests.get_all_tests_use_case import (
    GetAllTestsUseCase,
)
from app.application.use_cases.tests.queries.get_paginated_full_tests.get_paginated_full_tests_use_case import (
    GetPaginatedFullTestsUseCase,
)
from app.application.use_cases.tests.queries.get_paginated_single_tests.get_paginated_single_tests_use_case import (
    GetPaginatedSingleTestsUseCase,
)
from app.application.use_cases.tests.queries.get_test_detail.get_test_detail_use_case import (
    GetTestDetailUseCase,
)
from app.application.use_cases.tests.queries.get_test_with_passages.get_test_with_passages_use_case import (
    GetTestWithPassagesUseCase,
)
from app.common.settings import settings
from app.infrastructure.llm.claude_test_generator_service import (
    ClaudeTestGeneratorService,
)
from app.infrastructure.ocr.claude_image_to_text_service import ClaudeImageToTextService
from app.infrastructure.query_services.sql_class_query_service import (
    SqlClassQueryService,
)
from app.infrastructure.query_services.sql_passage_query_service import (
    SqlPassageQueryService,
)
from app.infrastructure.query_services.sql_test_query_service import (
    SQLTestQueryService,
)
from app.infrastructure.query_services.sql_user_query_service import SQLUserQueryService
from app.infrastructure.repositories.sql_class_repository import SQLClassRepository
from app.infrastructure.repositories.sql_passage_repository import (
    SQLPassageRepositoryInterface,
)
from app.infrastructure.repositories.sql_refresh_token_repository import (
    SQLRefreshTokenRepositoryInterface,
)
from app.infrastructure.repositories.sql_test_repository import SQLTestRepository
from app.infrastructure.repositories.sql_user_repository import (
    SqlUserRepositoryInterface,
)
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher_service import PasswordHasher


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

    # Repositories as Factories (session will be provided at call time)
    passage_repository = providers.Factory(SQLPassageRepositoryInterface)
    test_repository = providers.Factory(SQLTestRepository)
    user_repository = providers.Factory(SqlUserRepositoryInterface)
    refresh_token_repository = providers.Factory(SQLRefreshTokenRepositoryInterface)
    class_repository = providers.Factory(SQLClassRepository)

    # Query Services (for optimized reads)
    test_query_service = providers.Factory(SQLTestQueryService)
    passage_query_service = providers.Factory(SqlPassageQueryService)
    user_query_service = providers.Factory(SQLUserQueryService)
    class_query_service = providers.Factory(SqlClassQueryService)

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
    create_complete_passage_use_case = providers.Factory(
        CreateCompletePassageUseCase, passage_repository=passage_repository
    )
    update_passage_use_case = providers.Factory(
        UpdatePassageUseCase,
        passage_repository=passage_repository,
        test_repository=test_repository,
    )

    get_passages_use_case = providers.Factory(
        GetPassagesUseCase, passage_repo=passage_repository
    )
    get_all_passages_use_case = providers.Factory(
        GetAllPassagesUseCase, passage_service=passage_service
    )
    get_passage_detail_by_id_use_case = providers.Factory(
        GetPassageDetailByIdUseCase, passage_query_service=passage_query_service
    )

    # OCR use cases
    extract_text_use_case = providers.Factory(
        ExtractTextFromImageUseCase, image_to_text_service=image_to_text_service
    )

    # Test use cases
    extract_test_from_images_use_case = providers.Factory(
        ExtractTestFromImagesUseCase, test_generator_service=test_generator_service
    )
    create_test_use_case = providers.Factory(
        CreateTestUseCase, test_repository=test_repository
    )
    add_passage_to_test_use_case = providers.Factory(
        AddPassageToTestUseCase,
        test_repository=test_repository,
        passage_repository=passage_repository,
    )
    get_all_tests_use_case = providers.Factory(
        GetAllTestsUseCase, test_query_service=test_query_service
    )
    remove_passage_use_case = providers.Factory(
        DeletePassageByIdUseCase,
        test_query_service=test_query_service,
        test_repository=test_repository,
    )
    get_test_by_id = providers.Factory(
        GetTestWithPassagesUseCase,
        test_query_service=test_query_service,
    )
    get_test_detail_by_id = providers.Factory(
        GetTestDetailUseCase,
        test_query_service=test_query_service,
    )
    publish_test_use_case = providers.Factory(
        PublishTestUseCase,
        test_repository=test_repository,
        test_query_service=test_query_service,
    )
    get_paginated_single_tests_use_case = providers.Factory(
        GetPaginatedSingleTestsUseCase, test_query_service=test_query_service
    )
    get_paginated_full_tests_use_case = providers.Factory(
        GetPaginatedFullTestsUseCase, test_query_service=test_query_service
    )

    # class use cases
    create_class_use_case = providers.Factory(
        CreateClassUseCase,
        user_repo=user_repository,
        class_repo=class_repository,
        user_query_service=user_query_service,
    )
    list_classes_use_case = providers.Factory(
        ListClassesUseCase,
        class_query_service=class_query_service,
    )
    get_class_by_id_use_case = providers.Factory(
        GetClassByIdUseCase,
        class_query_service=class_query_service,
    )
    enroll_student_use_case = providers.Factory(
        EnrollStudentUseCase,
        class_query_service=class_query_service,
        class_repo=class_repository,
        user_repo=user_repository,
    )
    remove_student_use_case = providers.Factory(
        RemoveStudentUseCase,
        class_query_service=class_query_service,
        class_repo=class_repository,
        user_repo=user_repository,
    )
    assign_teacher_use_case = providers.Factory(
        AssignTeacherUseCase,
        class_repo=class_repository,
        user_repo=user_repository,
        class_query_service=class_query_service,
    )
    remove_teacher_use_case = providers.Factory(
        RemoveTeacherUseCase,
        class_query_service=class_query_service,
        class_repo=class_repository,
        user_repo=user_repository,
    )


# Global container instance
container = ApplicationContainer()
