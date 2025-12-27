from app.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.use_cases.auth.login.login_use_case import LoginUseCase


class AuthController:
    def __init__(self, login_use_case: LoginUseCase):
        self.login_use_case = login_use_case

    async def login(self, request: LoginRequest) -> LoginResponse:
        return await self.login_use_case.execute(request)