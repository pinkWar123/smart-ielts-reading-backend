from dependency_injector.wiring import Provide
from fastapi import APIRouter
from fastapi.params import Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.infrastructure.security.jwt_service import JwtService

router = APIRouter()

get_jwt_service = make_service_dependency(Provide[ApplicationContainer.jwt_service])

@router.get("/test", response_model=str)
async def test(
        jwt_service: JwtService = Depends(get_jwt_service)
):
    return jwt_service.log_secret()