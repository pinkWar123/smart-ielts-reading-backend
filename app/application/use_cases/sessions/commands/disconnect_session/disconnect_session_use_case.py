from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.application.use_cases.sessions.commands.disconnect_session.disconnect_session_dto import (
    DisconnectSessionRequest,
    DisconnectSessionResponse,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.session_errors import (
    NoPermissionToJoinSessionError,
    SessionNotFoundError,
    StudentNotInSessionError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.web_socket import ParticipantDisconnectedMessage


class DisconnectSessionUseCase(
    AuthenticatedUseCase[DisconnectSessionRequest, DisconnectSessionResponse]
):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        session_repo: SessionRepositoryInterface,
        connection_manager: ConnectionManagerServiceInterface,
    ):
        self.user_repo = user_repo
        self.session_repo = session_repo
        self.connection_manager = connection_manager

    async def execute(
        self, request: DisconnectSessionRequest, user_id: str
    ) -> DisconnectSessionResponse:
        user = await self._validate_and_fetch_user(user_id)
        session = await self._validate_and_fetch_session(request.session_id)

        await self._validate_user_permission(user, session)
        session.student_disconnect(user_id)

        updated_session = await self.session_repo.update(session)
        await self._broadcast_disconnect_message(user_id, updated_session)

        return DisconnectSessionResponse(
            session_id=updated_session.id,
            student_id=user_id,
            success=True,
            connected_count=updated_session.get_connected_student_count(),
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

        if not session.is_student_in_session(user.id):
            raise StudentNotInSessionError(student_id=user.id, session_id=session.id)

    async def _broadcast_disconnect_message(self, student_id: str, session: Session):
        await self.connection_manager.broadcast_to_session(
            session_id=session.id,
            message=ParticipantDisconnectedMessage(
                type="participant_disconnected",
                session_id=session.id,
                timestamp=TimeHelper.utc_now(),
                student_id=student_id,
                connected_count=session.get_connected_student_count(),
            ).dict(),
        )
