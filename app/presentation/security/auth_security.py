from alembic.util import status
from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.application.services.token_service import TokenService
from app.common.di import make_service_dependency
from app.container import ApplicationContainer

security = HTTPBearer()

get_token_service = make_service_dependency(Provide[ApplicationContainer.jwt_service])


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service),
):
    token = credentials.credentials

    try:
        payload = token_service.decode(token)
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
