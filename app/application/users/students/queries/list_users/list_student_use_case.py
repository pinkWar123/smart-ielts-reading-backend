from app.application.services.query.users.user_query_service import UserQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.users.students.queries.list_users.list_users_dto import (
    ListUserQuery,
    ListUsersResponse,
    UserDTO,
)
from app.domain.aggregates.users.user import UserRole


class ListUsersUseCase(UseCase[ListUserQuery, ListUsersResponse]):
    def __init__(self, user_query_service: UserQueryService):
        self.user_query_service = user_query_service

    async def execute(self, request: ListUserQuery) -> ListUsersResponse:
        students = await self.user_query_service.search_users(
            query=request.search, role=request.role, limit=request.limit
        )

        user_dtos = [
            UserDTO(
                id=s.id,
                username=s.username,
                full_name=s.full_name,
                email=str(s.email),
                role=s.role,
            )
            for s in students
        ]

        return ListUsersResponse(users=user_dtos)
