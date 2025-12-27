from app.application.services.token_service import TokenService
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_service import JwtService
from app.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.use_cases.base.use_case import RequestType, ResponseType, UseCase


class LoginUseCase(UseCase[LoginRequest, LoginResponse]):
    def __init__(self, user_repo: UserRepository, jwt_service: TokenService):
        self.user_repo = user_repo
        self.jwt_service = jwt_service

    async def execute(self, request: LoginRequest) -> LoginResponse:
        user = await self.user_repo.get_by_password(request.username, request.password)
        if user is None:
            raise UserNotFoundError()

        payload = {"user_id": user.id, "role": user.role, "username": user.username}
        access_token, refresh_token = self.jwt_service.create_token_pair(user.id, payload)

        response = LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=user.id,
            username=user.username,
        )

        return response
