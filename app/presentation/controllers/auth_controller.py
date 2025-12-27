from app.use_cases.auth.get_current_user.get_current_user_dto import (
    GetCurrentUserQuery,
    GetCurrentUserResponse,
)
from app.use_cases.auth.get_current_user.get_current_user_use_case import (
    GetCurrentUserUseCase,
)
from app.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.use_cases.auth.login.login_use_case import LoginUseCase
from app.use_cases.auth.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.use_cases.auth.regenerate_tokens.regenerate_tokens_use_case import (
    RegenerateTokensUseCase,
)
from app.use_cases.auth.register.register_dto import RegisterRequest, RegisterResponse
from app.use_cases.auth.register.register_use_case import RegisterUseCase


class AuthController:
    def __init__(
        self,
        login_use_case: LoginUseCase,
        register_use_case: RegisterUseCase,
        get_me_use_case: GetCurrentUserUseCase,
        regenerate_tokens_use_case: RegenerateTokensUseCase,
    ):
        self.login_use_case = login_use_case
        self.register_use_case = register_use_case
        self.get_me_use_case = get_me_use_case
        self.regenerate_tokens_use_case = regenerate_tokens_use_case

    async def login(self, request: LoginRequest) -> LoginResponse:
        return await self.login_use_case.execute(request)

    async def register(self, request: RegisterRequest) -> RegisterResponse:
        return await self.register_use_case.execute(request)

    async def get_me(self, token: str) -> GetCurrentUserResponse:
        query = GetCurrentUserQuery(access_token=token)
        return await self.get_me_use_case.execute(query)

    async def regenerate_tokens(
        self, request: RegenerateTokensRequest
    ) -> RegenerateTokensResponse:
        return await self.regenerate_tokens_use_case.execute(request)
