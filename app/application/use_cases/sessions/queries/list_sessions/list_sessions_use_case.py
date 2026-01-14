from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_dto import (
    ListSessionsQuery,
    ListSessionsResponse,
    SessionSummaryDTO,
)
from app.domain.repositories.session_repository import SessionRepositoryInterface


class ListSessionsUseCase(UseCase[ListSessionsQuery, ListSessionsResponse]):
    def __init__(self, session_repo: SessionRepositoryInterface):
        self.session_repo = session_repo

    async def execute(self, request: ListSessionsQuery) -> ListSessionsResponse:
        # Get sessions based on filter
        if request.teacher_id:
            sessions = await self.session_repo.get_by_teacher(request.teacher_id)
        elif request.class_id:
            sessions = await self.session_repo.get_by_class(request.class_id)
        else:
            # No filter - get active sessions (admin use case)
            sessions = await self.session_repo.get_active_sessions()

        # Convert to summary DTOs
        session_summaries = [
            SessionSummaryDTO(
                id=s.id,
                class_id=s.class_id,
                test_id=s.test_id,
                title=s.title,
                scheduled_at=s.scheduled_at,
                started_at=s.started_at,
                completed_at=s.completed_at,
                status=s.status,
                participant_count=len(s.participants),
                created_by=s.created_by,
                created_at=s.created_at,
            )
            for s in sessions
        ]

        return ListSessionsResponse(sessions=session_summaries)
