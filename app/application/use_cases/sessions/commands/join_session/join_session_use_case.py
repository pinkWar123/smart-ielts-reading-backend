from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.application.use_cases.sessions.commands.join_session.join_session_dto import (
    SessionJoinRequest,
    SessionJoinResponse,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.session_errors import (
    NoPermissionToJoinSessionError,
    SessionNotFoundError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.web_socket import ParticipantJoinedMessage


class JoinSessionUseCase(AuthenticatedUseCase[SessionJoinRequest, SessionJoinResponse]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        session_repo: SessionRepositoryInterface,
        class_repo: ClassRepositoryInterface,
        connection_manager: ConnectionManagerServiceInterface,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.class_repo = class_repo
        self.connection_manager = connection_manager

    async def execute(
        self, request: SessionJoinRequest, user_id: str
    ) -> SessionJoinResponse:
        user = await self._validate_and_fetch_user(user_id)
        session = await self._validate_and_fetch_session(request.session_id)

        await self._validate_user_permission(user, session)
        session.student_join(user_id)

        updated_session = await self.session_repo.update(session)
        await self._broadcast_session_update(
            user_id, updated_session.id, len(updated_session.participants)
        )

        return SessionJoinResponse(
            session_id=updated_session.id,
            participant_id=updated_session.id,
            success=len(session.participants) < len(updated_session.participants),
        )

    async def _validate_and_fetch_user(self, user_id: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user.to_domain()

    async def _validate_and_fetch_session(self, session_id: str) -> Session:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        return session

    async def _validate_user_permission(self, user: User, session: Session):
        if user.role != UserRole.STUDENT:
            raise NoPermissionToJoinSessionError(user_id=user.id, session_id=session.id)

        participant_ids = [p.student_id for p in session.participants]

        if user.id not in participant_ids:
            raise NoPermissionToJoinSessionError(user_id=user.id, session_id=session.id)

    async def _broadcast_session_update(
        self, student_id: str, session_id: str, connected_count: int
    ):
        await self.connection_manager.broadcast_to_session(
            session_id=session_id,
            message=ParticipantJoinedMessage(
                type="participant_joined",
                session_id=session_id,
                timestamp=TimeHelper.utc_now(),
                student_id=student_id,
                connected_count=connected_count,
            ).dict(),
        )
