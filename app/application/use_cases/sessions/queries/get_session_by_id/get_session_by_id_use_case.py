from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_dto import (
    GetSessionByIdQuery,
    GetSessionByIdResponse,
    ParticipantDetailDTO,
)
from app.domain.errors.session_errors import SessionNotFoundError
from app.domain.repositories.session_repository import SessionRepositoryInterface


class GetSessionByIdUseCase(UseCase[GetSessionByIdQuery, GetSessionByIdResponse]):
    def __init__(self, session_repo: SessionRepositoryInterface):
        self.session_repo = session_repo

    async def execute(self, request: GetSessionByIdQuery) -> GetSessionByIdResponse:
        # Get session by ID
        session = await self.session_repo.get_by_id(request.session_id)

        if not session:
            raise SessionNotFoundError(request.session_id)

        # Convert to response DTO
        return GetSessionByIdResponse(
            id=session.id,
            test_id=session.test_id,
            title=session.title,
            scheduled_at=session.scheduled_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
            status=session.status,
            participants=[
                ParticipantDetailDTO(
                    student_id=p.student_id,
                    attempt_id=p.attempt_id,
                    joined_at=p.joined_at,
                    connection_status=p.connection_status,
                    last_activity=p.last_activity,
                )
                for p in session.participants
            ],
            created_by=session.created_by,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )
