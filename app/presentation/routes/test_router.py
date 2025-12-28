from dependency_injector.wiring import Provide
from fastapi import APIRouter
from fastapi.params import Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.infrastructure.security.jwt_service import JwtService

router = APIRouter()

get_jwt_service = make_service_dependency(Provide[ApplicationContainer.jwt_service])


@router.get(
    "",
    response_model=str,
    summary="Health Check",
    description="Test endpoint to verify JWT service functionality",
    responses={
        200: {"description": "Service is running - returns JWT secret information"},
        500: {"description": "Internal server error - service unavailable"},
    },
)
async def test(jwt_service: JwtService = Depends(get_jwt_service)):
    """
    Health check endpoint for JWT service testing.

    This endpoint is primarily used for:
    - Development and debugging purposes
    - Verifying JWT service configuration
    - Testing dependency injection

    **Note**: This endpoint should be disabled in production environments
    as it may expose sensitive configuration information.

    Returns JWT service status and configuration details.
    """
    return jwt_service.log_secret()
