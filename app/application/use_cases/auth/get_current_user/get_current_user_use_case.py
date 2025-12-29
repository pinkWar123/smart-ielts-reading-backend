from app.application.services.token_service import TokenService
from app.application.use_cases.auth.get_current_user.get_current_user_dto import (
    GetCurrentUserQuery,
    GetCurrentUserResponse,
)
from app.application.use_cases.base.use_case import ResponseType, UseCase


class GetCurrentUserUseCase(UseCase[GetCurrentUserQuery, GetCurrentUserResponse]):
    def __init__(self, token_service: TokenService):
        self.token_service = token_service

    def execute(self, query: GetCurrentUserQuery) -> ResponseType:
        access_token = query.access_token
        payload = self.token_service.decode(access_token)

        return GetCurrentUserResponse(
            username=payload.get("username"),
            role=payload.get("role"),
            user_id=payload.get("user_id"),
            email=payload.get("email"),
            full_name=payload.get("full_name"),
            exp=payload.get("exp"),
        )
