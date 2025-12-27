from dependency_injector.wiring import Provide
from fastapi import APIRouter
from fastapi.params import Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.auth_controller import AuthController
from app.use_cases.auth.login.login_dto import LoginResponse, LoginRequest
from app.use_cases.auth.login.login_use_case import LoginUseCase

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
    return LoginResponse(
        access_token=result.access_token, refresh_token=result.refresh_token,
    user_id=result.user_id, username=result.username)
