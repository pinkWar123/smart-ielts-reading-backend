from app.application.services.token_service import TokenService
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.user_repository import UserRepository
from app.use_cases.auth.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.use_cases.base.use_case import RequestType, ResponseType, UseCase


class RegenerateTokensUseCase(
    UseCase[RegenerateTokensRequest, RegenerateTokensResponse]
):
    def __init__(self, token_service: TokenService, user_repo: UserRepository):
        self.token_service = token_service
        self.user_repo = user_repo

    async def execute(
        self, request: RegenerateTokensRequest
    ) -> RegenerateTokensResponse:
        user_model = await self.user_repo.get_by_id(request.user_id)
        if user_model is None:
            raise UserNotFoundError()

        await self.token_service.validate_refresh_token(
            request.refresh_token, request.user_id
        )

        access_token, refresh_token = await self.token_service.create_token_pair(
            user_model.to_domain(), {}
        )

        return RegenerateTokensResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=user_model.id,
            username=user_model.username,
            full_name=user_model.full_name,
            role=user_model.role.value,
        )
