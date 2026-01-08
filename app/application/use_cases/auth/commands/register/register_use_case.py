from app.application.services.token_service import TokenService
from app.application.use_cases.auth.commands.register.register_dto import (
    RegisterRequest,
    RegisterResponse,
)
from app.application.use_cases.base.use_case import UseCase
from app.domain.entities.user import User
from app.domain.errors.user_errors import (
    EmailAlreadyBeenUsedError,
    UsernameAlreadyExistsError,
)
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.security.password_hasher_service import PasswordHasher


class RegisterUseCase(UseCase[RegisterRequest, RegisterResponse]):
    async def execute(self, request: RegisterRequest) -> RegisterResponse:
        existing_user = await self.user_repo.find(request.username, str(request.email))
        if existing_user:
            if existing_user.username == request.username:
                raise UsernameAlreadyExistsError()
            elif existing_user.email == request.email:
                raise EmailAlreadyBeenUsedError()
        hashed_password = self.password_hasher.hash(request.password)

        user = User(
            username=request.username,
            email=request.email,
            password_hash=hashed_password,
            full_name=request.full_name,
            role=request.role,
        )

        user_model = await self.user_repo.create(user)
        user = user_model.to_domain()
        access_token, refresh_token = await self.token_service.create_token_pair(
            user, {}
        )
        return RegisterResponse(
            access_token=access_token,
            refresh_token=refresh_token.token,
            user_id=user_model.id,
            username=user_model.username,
            role=user_model.role.value,
            email=user_model.email,
            full_name=user_model.full_name,
        )

    def __init__(
        self,
        user_repo: UserRepositoryInterface,
        token_service: TokenService,
        password_hasher: PasswordHasher,
    ):
        self.user_repo = user_repo
        self.token_service = token_service
        self.password_hasher = password_hasher
