from dependency_injector.wiring import Provide
from fastapi import APIRouter
from fastapi.params import Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.security.auth_security import verify_token
from app.use_cases.auth.get_current_user.get_current_user_dto import (
    GetCurrentUserResponse,
)
from app.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.use_cases.auth.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.use_cases.auth.register.register_dto import RegisterRequest, RegisterResponse

router = APIRouter()

get_auth_controller = make_service_dependency(
    Provide[ApplicationContainer.auth_controller]
)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.login(request)
    return result


@router.post("/register", response_model=RegisterResponse)
async def register(
    request: RegisterRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.register(request)
    return result


@router.get("/me", response_model=GetCurrentUserResponse)
async def get_me(current_user=Depends(verify_token)):
    return current_user


@router.post("/refresh-tokens", response_model=RegenerateTokensResponse)
async def regenerate_tokens(
    request: RegenerateTokensRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    result = await controller.regenerate_tokens(request)
    return result
