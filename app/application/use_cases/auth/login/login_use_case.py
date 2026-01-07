from app.application.services.password_service import PasswordService
from app.application.services.token_service import TokenService
from app.application.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.application.use_cases.base.use_case import UseCase
from app.domain.errors.user_errors import UserNotFoundError, WrongPasswordError
from app.domain.repositories.user_repository import UserRepositoryInterface


class LoginUseCase(UseCase[LoginRequest, LoginResponse]):
    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        jwt_service: TokenService,
        password_hasher: PasswordService,
    ):
        self.user_repo = user_repo
        self.jwt_service = jwt_service
        self.password_hasher = password_hasher

    async def execute(self, request: LoginRequest) -> LoginResponse:
        user = await self.user_repo.get_by_username(request.username)
        if user is None:
            raise UserNotFoundError()

        is_password_valid = self.password_hasher.verify(
            request.password, user.password_hash
        )
        if not is_password_valid:
            raise WrongPasswordError()

        access_token, refresh_token = await self.jwt_service.create_token_pair(
            user, None
        )

        response = LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=user.id,
            username=user.username,
            role=user.role.value,
            email=user.email,
            full_name=user.full_name,
        )

        return response
