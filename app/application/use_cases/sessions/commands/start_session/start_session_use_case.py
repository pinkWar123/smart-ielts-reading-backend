from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.application.use_cases.sessions.commands.start_session.start_session_dto import (
    ParticipantDTO,
    StartSessionRequest,
    StartSessionResponse,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session
from app.domain.aggregates.session.constants import CONNECTION_STATUS_CONNECTED
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.class_errors import ClassNotFoundError
from app.domain.errors.session_errors import (
    NoPermissionToManageSessionError,
    SessionNotFoundError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.web_socket import SessionStartedMessage


class StartSessionUseCase(
    AuthenticatedUseCase[StartSessionRequest, StartSessionResponse]
):

    def __init__(
        self,
        session_repo: SessionRepositoryInterface,
        class_repo: ClassRepositoryInterface,
        user_repo: UserRepositoryInterface,
        connection_manager: ConnectionManagerServiceInterface,
    ):
        self.session_repo = session_repo
        self.class_repo = class_repo
        self.user_repo = user_repo
        self.connection_manager = connection_manager

    async def execute(
        self, request: StartSessionRequest, user_id: str
    ) -> StartSessionResponse:
        user = await self._validate_and_fetch_user(user_id)
        session = await self._validate_and_fetch_session(request.session_id)

        if user.role == UserRole.TEACHER:
            await self._validate_teacher_access(
                teacher_id=user_id, class_id=session.class_id
            )
        elif user.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise NoPermissionToManageSessionError(
                user_id=user_id, session_id=request.session_id
            )

        session.start_session()

        updated_session = await self.session_repo.update(session)

        await self._broadcast_session_update(updated_session)

        return StartSessionResponse(
            id=updated_session.id,
            class_id=updated_session.class_id,
            test_id=updated_session.test_id,
            title=updated_session.title,
            scheduled_at=updated_session.scheduled_at,
            started_at=updated_session.started_at,
            completed_at=updated_session.completed_at,
            status=updated_session.status,
            participants=[
                ParticipantDTO(
                    student_id=p.student_id,
                    attempt_id=p.attempt_id,
                    joined_at=p.joined_at,
                    connection_status=p.connection_status,
                    last_activity=p.last_activity,
                )
                for p in updated_session.participants
            ],
            created_by=updated_session.created_by,
            created_at=updated_session.created_at,
            updated_at=updated_session.updated_at,
        )

    async def _validate_and_fetch_user(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user.to_domain()

    async def _validate_teacher_access(self, teacher_id: str, class_id: str):
        class_entity = await self.class_repo.get_by_id(class_id)
        if not class_entity:
            raise ClassNotFoundError(class_id=class_id)
        if teacher_id not in class_entity.teacher_ids:
            raise NoPermissionToManageSessionError(
                user_id=teacher_id, session_id="session"
            )

    async def _validate_and_fetch_session(self, session_id: str) -> Session:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)
        return session

    async def _broadcast_session_update(self, session: Session):
        await self.connection_manager.broadcast_to_session(
            session_id=session.id,
            message=SessionStartedMessage(
                type="session_started",
                session_id=session.id,
                timestamp=TimeHelper.utc_now(),
                started_at=session.started_at,
                connected_students=[
                    p.student_id
                    for p in session.participants
                    if p.connection_status == CONNECTION_STATUS_CONNECTED
                ],
            ).dict(),
        )
