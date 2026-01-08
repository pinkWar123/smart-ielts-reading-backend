from fastapi import APIRouter
from fastapi.params import Depends

from app.application.use_cases.auth.commands.login.login_dto import (
    LoginRequest,
    LoginResponse,
)
from app.application.use_cases.auth.commands.regenerate_tokens.regenerate_tokens_dto import (
    RegenerateTokensRequest,
    RegenerateTokensResponse,
)
from app.application.use_cases.auth.commands.register.register_dto import (
    RegisterRequest,
    RegisterResponse,
)
from app.application.use_cases.auth.queries.get_current_user.get_current_user_dto import (
    GetCurrentUserResponse,
)
from app.common.dependencies import AuthUseCases, get_auth_use_cases
from app.presentation.security.dependencies import require_auth

router = APIRouter()


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
    use_cases: AuthUseCases = Depends(get_auth_use_cases),
):
    """
    Authenticate user with credentials:

    - **email**: Valid email address (required)
    - **password**: User password (required)

    Returns JWT access token for API authentication and refresh token for token renewal.
    Access tokens have a limited lifespan and need to be refreshed using the refresh token.
    """
    return await use_cases.login.execute(request)


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
    use_cases: AuthUseCases = Depends(get_auth_use_cases),
):
    """
    Register a new user account:

    - **email**: Must be unique and valid email format (required)
    - **password**: User password with minimum security requirements (required)
    - **username**: Optional display name for the user

    After successful registration, the user will receive authentication tokens
    and can immediately start using protected endpoints.
    """
    return await use_cases.register.execute(request)


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
    use_cases: AuthUseCases = Depends(get_auth_use_cases),
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
    return await use_cases.regenerate_tokens.execute(request)
