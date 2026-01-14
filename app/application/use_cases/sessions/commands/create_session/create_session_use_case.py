from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.application.use_cases.sessions.commands.create_session.create_session_dto import (
    CreateSessionRequest,
    CreateSessionResponse,
    ParticipantDTO,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session, SessionParticipant, SessionStatus
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import NoPermissionToCreateSessionError
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class CreateSessionUseCase(
    AuthenticatedUseCase[CreateSessionRequest, CreateSessionResponse]
):
    def __init__(
        self,
        session_repo: SessionRepositoryInterface,
        class_repo: ClassRepositoryInterface,
        test_repo: TestRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.session_repo = session_repo
        self.class_repo = class_repo
        self.test_repo = test_repo
        self.user_repo = user_repo

    async def execute(
        self, request: CreateSessionRequest, user_id: str
    ) -> CreateSessionResponse:
        # Validate creator permissions
        creator = await self._validate_creator_permissions(user_id)

        # Validate class exists and user has access
        class_entity = await self._validate_class_access(request.class_id, user_id)

        # Validate test exists
        await self._validate_test_exists(request.test_id)

        # Initialize participants from class student roster
        participants = [
            SessionParticipant(
                student_id=student_id,
                attempt_id=None,
                joined_at=None,
                connection_status="DISCONNECTED",
                last_activity=None,
            )
            for student_id in class_entity.student_ids
        ]

        # Create session aggregate
        new_session = Session(
            class_id=request.class_id,
            test_id=request.test_id,
            title=request.title,
            scheduled_at=request.scheduled_at,
            status=SessionStatus.SCHEDULED,
            participants=participants,
            created_by=user_id,
            created_at=TimeHelper.utc_now(),
        )

        # Persist session
        session_entity = await self.session_repo.create(new_session)

        # Convert to response
        return CreateSessionResponse(
            id=session_entity.id,
            class_id=session_entity.class_id,
            test_id=session_entity.test_id,
            title=session_entity.title,
            scheduled_at=session_entity.scheduled_at,
            status=session_entity.status,
            participants=[
                ParticipantDTO(
                    student_id=p.student_id,
                    attempt_id=p.attempt_id,
                    joined_at=p.joined_at,
                    connection_status=p.connection_status,
                    last_activity=p.last_activity,
                )
                for p in session_entity.participants
            ],
            created_by=session_entity.created_by,
            created_at=session_entity.created_at,
        )

    async def _validate_creator_permissions(self, user_id: str):
        """Validate that the creator exists and has permission to create sessions"""
        creator = await self.user_repo.get_by_id(user_id)
        if not creator:
            raise UserNotFoundError(user_id)
        if creator.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise NoPermissionToCreateSessionError(user_id=user_id)
        return creator

    async def _validate_class_access(self, class_id: str, user_id: str):
        """Validate class exists and user has access to it"""
        class_entity = await self.class_repo.get_by_id(class_id)
        if not class_entity:
            raise ClassNotFoundError(class_id=class_id)

        # Check if user is a teacher in this class or is an admin
        creator = await self.user_repo.get_by_id(user_id)
        if creator.role != UserRole.ADMIN and user_id not in class_entity.teacher_ids:
            raise NoPermissionToCreateSessionError(user_id=user_id)

        return class_entity

    async def _validate_test_exists(self, test_id: str):
        """Validate that the test exists"""
        test = await self.test_repo.get_by_id(test_id)
        if not test:
            raise TestNotFoundError(test_id=test_id)
