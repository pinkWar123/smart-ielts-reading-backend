from anthropic import AsyncAnthropic
from dependency_injector import containers, providers

from app.application.services.passage_service import PassageService
from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_use_case import (
    RecordHighlightUseCase,
)
from app.application.use_cases.attempts.commands.progress.record_violation.record_violation_use_case import (
    RecordViolationUseCase,
)
from app.application.use_cases.attempts.commands.progress.update_answer.update_answer_use_case import (
    UpdateAnswerUseCase,
)
from app.application.use_cases.attempts.commands.progress.update_progress.update_progress_use_case import (
    UpdateProgressUseCase,
)
from app.application.use_cases.attempts.commands.submit.submit_attempt_use_case import (
    SubmitAttemptUseCase,
)
from app.application.use_cases.attempts.queries.get_by_id.get_by_id_use_case import (
    GetAttemptByIdUseCase,
)
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
from app.application.use_cases.classes.commands.update_class.update_class_use_case import (
    UpdateClassUseCase,
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
from app.application.use_cases.sessions.commands.cancel_session.cancel_session_use_case import (
    CancelledSessionUseCase,
)
from app.application.use_cases.sessions.commands.complete_session.complete_session_use_case import (
    CompleteSessionUseCase,
)
from app.application.use_cases.sessions.commands.create_session.create_session_use_case import (
    CreateSessionUseCase,
)
from app.application.use_cases.sessions.commands.disconnect_session.disconnect_session_use_case import (
    DisconnectSessionUseCase,
)
from app.application.use_cases.sessions.commands.join_session.join_session_use_case import (
    JoinSessionUseCase,
)
from app.application.use_cases.sessions.commands.start_session.start_session_use_case import (
    StartSessionUseCase,
)
from app.application.use_cases.sessions.commands.start_waiting.start_waiting_use_case import (
    StartWaitingUseCase,
)
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_use_case import (
    GetMySessionsUseCase,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_use_case import (
    GetSessionByIdUseCase,
)
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_use_case import (
    ListSessionsUseCase,
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
from app.application.users.students.queries.list_users.list_student_use_case import (
    ListUsersUseCase,
)
from app.common.settings import settings
from app.infrastructure.llm.claude_test_generator_service import (
    ClaudeTestGeneratorService,
)
from app.infrastructure.ocr.claude_image_to_text_service import ClaudeImageToTextService
from app.infrastructure.query_services.sql_attempt_query_service import (
    SQLAttemptQueryService,
)
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
from app.infrastructure.repositories.sql_attempt_repository import SQLAttemptRepository
from app.infrastructure.repositories.sql_class_repository import SQLClassRepository
from app.infrastructure.repositories.sql_passage_repository import (
    SQLPassageRepositoryInterface,
)
from app.infrastructure.repositories.sql_refresh_token_repository import (
    SQLRefreshTokenRepositoryInterface,
)
from app.infrastructure.repositories.sql_session_repository import SQLSessionRepository
from app.infrastructure.repositories.sql_test_repository import SQLTestRepository
from app.infrastructure.repositories.sql_user_repository import (
    SqlUserRepositoryInterface,
)
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.security.password_hasher_service import PasswordHasher
from app.infrastructure.web_socket.in_memory_connection_manager import (
    InMemoryConnectionManagerService,
)


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
    session_repository = providers.Factory(SQLSessionRepository)
    attempt_repository = providers.Factory(SQLAttemptRepository)

    # Query Services (for optimized reads)
    test_query_service = providers.Factory(SQLTestQueryService)
    passage_query_service = providers.Factory(SqlPassageQueryService)
    user_query_service = providers.Factory(SQLUserQueryService)
    class_query_service = providers.Factory(SqlClassQueryService)
    attempt_query_service = providers.Factory(SQLAttemptQueryService)

    # Services
    passage_service = providers.Factory(PassageService, passage_repo=passage_repository)
    jwt_service = providers.Factory(
        JwtService, settings=settings, refresh_token_repo=refresh_token_repository
    )
    password_hasher = providers.Singleton(PasswordHasher)
    connection_manager = providers.Singleton(InMemoryConnectionManagerService)

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
    update_class_use_case = providers.Factory(
        UpdateClassUseCase,
        class_query_service=class_query_service,
        class_repo=class_repository,
        user_repo=user_repository,
    )

    # Session use cases
    create_session_use_case = providers.Factory(
        CreateSessionUseCase,
        session_repo=session_repository,
        class_repo=class_repository,
        test_repo=test_repository,
        user_repo=user_repository,
    )
    list_sessions_use_case = providers.Factory(
        ListSessionsUseCase,
        session_repo=session_repository,
    )
    get_session_by_id_use_case = providers.Factory(
        GetSessionByIdUseCase,
        session_repo=session_repository,
    )
    get_my_sessions_use_case = providers.Factory(
        GetMySessionsUseCase,
        session_repo=session_repository,
    )
    start_session_use_case = providers.Factory(
        StartSessionUseCase,
        session_repo=session_repository,
        class_repo=class_repository,
        user_repo=user_repository,
        connection_manager=connection_manager,
    )
    start_waiting_use_case = providers.Factory(
        StartWaitingUseCase,
        session_repo=session_repository,
        class_repo=class_repository,
        user_repo=user_repository,
        connection_manager=connection_manager,
    )
    cancel_session_use_case = providers.Factory(
        CancelledSessionUseCase,
        session_repo=session_repository,
        user_repo=user_repository,
        class_repo=class_repository,
        connection_manager=connection_manager,
    )
    complete_session_use_case = providers.Factory(
        CompleteSessionUseCase,
        session_repo=session_repository,
        user_repo=user_repository,
        class_repo=class_repository,
        connection_manager=connection_manager,
    )

    join_session_use_case = providers.Factory(
        JoinSessionUseCase,
        session_repo=session_repository,
        user_repo=user_repository,
        class_repo=class_repository,
        connection_manager=connection_manager,
    )
    disconnect_session_use_case = providers.Factory(
        DisconnectSessionUseCase,
        user_repo=user_repository,
        session_repo=session_repository,
        connection_manager=connection_manager,
    )

    # Attempt use cases
    get_attempt_by_id_use_case = providers.Factory(
        GetAttemptByIdUseCase, attempt_query_service=attempt_query_service
    )
    update_answer_use_case = providers.Factory(
        UpdateAnswerUseCase,
        test_query_service=test_query_service,
        attempt_repo=attempt_repository,
    )
    update_progress_use_case = providers.Factory(
        UpdateProgressUseCase,
        attempt_repo=attempt_repository,
    )
    record_highlight_use_case = providers.Factory(
        RecordHighlightUseCase,
        attempt_repo=attempt_repository,
    )
    record_violation_use_case = providers.Factory(
        RecordViolationUseCase,
        attempt_repo=attempt_repository,
        connection_manager=connection_manager,
    )
    submit_attempt_use_case = providers.Factory(
        SubmitAttemptUseCase,
        attempt_repo=attempt_repository,
        test_query_service=test_query_service,
    )

    # User use cases
    list_users_use_case = providers.Factory(
        ListUsersUseCase,
        user_query_service=user_query_service,
    )


# Global container instance
container = ApplicationContainer()
