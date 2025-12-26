from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.passage_controller import PassageController
from app.use_cases.passages.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)

router = APIRouter()

get_passage_controller = make_service_dependency(
    Provide[ApplicationContainer.passage_controller]
)


@router.post("/passages", response_model=PassageResponse)
async def create_passage(
    request: CreatePassageRequest,
    controller: PassageController = Depends(get_passage_controller),
):
    return await controller.create_passage(request)


@router.get("/passages", response_model=list[PassageResponse])
async def get_all_passages(
    controller: PassageController = Depends(get_passage_controller),
):
    return await controller.get_all_passages()
