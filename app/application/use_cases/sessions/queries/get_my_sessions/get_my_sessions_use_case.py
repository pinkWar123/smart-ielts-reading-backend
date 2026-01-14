from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_dto import (
    GetMySessionsQuery,
    GetMySessionsResponse,
    MySessionDTO,
)
from app.domain.repositories.session_repository import SessionRepositoryInterface


class GetMySessionsUseCase(UseCase[GetMySessionsQuery, GetMySessionsResponse]):
    def __init__(self, session_repo: SessionRepositoryInterface):
        self.session_repo = session_repo

    async def execute(self, request: GetMySessionsQuery) -> GetMySessionsResponse:
        # Get all sessions where student is a participant
        sessions = await self.session_repo.get_by_student(request.student_id)

        # Convert to DTOs with student-specific info
        my_sessions = []
        for s in sessions:
            # Find this student's participant info
            my_participant = next(
                (p for p in s.participants if p.student_id == request.student_id), None
            )

            if my_participant:
                my_sessions.append(
                    MySessionDTO(
                        id=s.id,
                        class_id=s.class_id,
                        test_id=s.test_id,
                        title=s.title,
                        scheduled_at=s.scheduled_at,
                        started_at=s.started_at,
                        completed_at=s.completed_at,
                        status=s.status,
                        my_attempt_id=my_participant.attempt_id,
                        my_joined_at=my_participant.joined_at,
                        my_connection_status=my_participant.connection_status,
                        created_at=s.created_at,
                    )
                )

        return GetMySessionsResponse(sessions=my_sessions)
