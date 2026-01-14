from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.application.use_cases.sessions.commands.complete_session.complete_session_dto import (
    CompleteSessionRequest,
    CompleteSessionResponse,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session
from app.domain.aggregates.users.user import User, UserRole
from app.domain.errors.session_errors import (
    NoPermissionToManageSessionError,
    SessionNotFoundError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class CompleteSessionUseCase(
    AuthenticatedUseCase[CompleteSessionRequest, CompleteSessionResponse]
):
    def __init__(
        self,
        session_repo: SessionRepositoryInterface,
        user_repo: UserRepositoryInterface,
        class_repo: ClassRepositoryInterface,
        connection_manager: ConnectionManagerServiceInterface,
    ):
        self.session_repo = session_repo
        self.user_repo = user_repo
        self.class_repo = class_repo
        self.connection_manager = connection_manager

    async def execute(
        self, request: CompleteSessionRequest, user_id: str
    ) -> CompleteSessionResponse:
        user = await self._validate_and_fetch_user(user_id)
        session = await self._validate_and_fetch_session(request.session_id)

        await self._validate_user_permission(user, session)
        session.complete_session()

        updated_session = await self.session_repo.update(session)

        return CompleteSessionResponse(
            session_id=updated_session.id,
            success=True,
            completed_at=updated_session.completed_at,
            completed_by=user_id,
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
        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToManageSessionError(
                user_id=user.id, session_id=session.id
            )

        if user.role == UserRole.TEACHER:
            # Fetch the class to check if teacher is authorized
            class_entity = await self.class_repo.get_by_id(session.class_id)
            if not class_entity or user.id not in class_entity.teacher_ids:
                raise NoPermissionToManageSessionError(
                    user_id=user.id, session_id=session.id
                )
