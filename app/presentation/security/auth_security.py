from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError

from app.application.services.token_service import TokenService
from app.common.dependencies import get_jwt_service

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_jwt_service),
):
    token = credentials.credentials
    return token_service.decode(token)
