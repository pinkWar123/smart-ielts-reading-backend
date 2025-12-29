from dependency_injector.wiring import Provide
from fastapi import APIRouter
from fastapi.params import Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.auth_controller import AuthController
from app.presentation.security.dependencies import require_auth
from app.application.use_cases.auth.get_current_user.get_current_user_dto import (
    GetCurrentUserResponse,
)
from app.application.use_cases.auth.login.login_dto import LoginRequest, LoginResponse
from app.application.use_cases.auth.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.application.use_cases.auth.register.register_dto import RegisterRequest, RegisterResponse

router = APIRouter()

get_auth_controller = make_service_dependency(
    Provide[ApplicationContainer.auth_controller]
)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate user with email and password",
    responses={
        200: {"description": "Login successful - returns access and refresh tokens"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error - invalid request format"},
    },
)
async def login(
    request: LoginRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    """
    Authenticate user with credentials:

    - **email**: Valid email address (required)
    - **password**: User password (required)

    Returns JWT access token for API authentication and refresh token for token renewal.
    Access tokens have a limited lifespan and need to be refreshed using the refresh token.
    """
    result = await controller.login(request)
    return result


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="User Registration",
    description="Create a new user account",
    status_code=201,
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "User already exists with this email"},
        422: {"description": "Validation error - invalid request format"},
    },
)
async def register(
    request: RegisterRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    """
    Register a new user account:

    - **email**: Must be unique and valid email format (required)
    - **password**: User password with minimum security requirements (required)
    - **username**: Optional display name for the user

    After successful registration, the user will receive authentication tokens
    and can immediately start using protected endpoints.
    """
    result = await controller.register(request)
    return result


@router.get(
    "/me",
    response_model=GetCurrentUserResponse,
    summary="Get Current User Profile",
    description="Retrieve authenticated user information",
    responses={
        200: {"description": "User profile information retrieved successfully"},
        401: {"description": "Authentication required - invalid or missing token"},
    },
)
async def get_me(current_user=require_auth):
    """
    Get current authenticated user profile information.

    This endpoint requires a valid JWT token in the Authorization header:
    `Authorization: Bearer <your_access_token>`

    Returns complete user profile including:
    - User ID
    - Email address
    - Username
    - Registration date
    - Last login information
    """
    return current_user


@router.post(
    "/refresh-tokens",
    response_model=RegenerateTokensResponse,
    summary="Refresh Access Token",
    description="Generate new access token using refresh token",
    responses={
        200: {"description": "Tokens refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
        422: {"description": "Validation error - invalid request format"},
    },
)
async def regenerate_tokens(
    request: RegenerateTokensRequest,
    controller: AuthController = Depends(get_auth_controller),
):
    """
    Refresh expired access token using a valid refresh token:

    - **refresh_token**: Valid refresh token received during login/registration (required)

    When your access token expires, use this endpoint to get a new access token
    without requiring the user to log in again. The refresh token has a longer
    lifespan than access tokens.

    Returns a new access token and refresh token pair. The old refresh token
    will be invalidated for security purposes.
    """
    result = await controller.regenerate_tokens(request)
    return result
