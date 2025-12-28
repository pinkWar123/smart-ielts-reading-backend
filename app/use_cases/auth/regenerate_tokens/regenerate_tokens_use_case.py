from app.application.services.token_service import TokenService
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.domain.repositories.user_repository import UserRepository
from app.use_cases.auth.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.use_cases.base.use_case import UseCase


class RegenerateTokensUseCase(
    UseCase[RegenerateTokensRequest, RegenerateTokensResponse]
):
    def __init__(
        self, token_service: TokenService, refresh_token_repo: RefreshTokenRepository
    ):
        self.token_service = token_service
        self.refresh_token_repo = refresh_token_repo

    async def execute(
        self, request: RegenerateTokensRequest
    ) -> RegenerateTokensResponse:
        await self.token_service.validate_refresh_token(request.refresh_token)

        associated_user = await self.refresh_token_repo.get_user_by_token(
            request.refresh_token
        )
        if associated_user is None:
            raise UserNotFoundError()

        access_token, refresh_token = await self.token_service.create_token_pair(
            associated_user.to_domain(), {}
        )

        return RegenerateTokensResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=associated_user.id,
            username=associated_user.username,
            full_name=associated_user.full_name,
            role=associated_user.role.value,
        )
