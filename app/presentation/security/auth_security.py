from dependency_injector.wiring import Provide
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError

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
    return token_service.decode(token)
