from dependency_injector.wiring import Provide
from fastapi import APIRouter, Depends

from app.application.use_cases.passages.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)
from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.passage_controller import PassageController
from app.presentation.security.dependencies import require_auth

router = APIRouter()

get_passage_controller = make_service_dependency(
    Provide[ApplicationContainer.passage_controller]
)


@router.post(
    "",
    response_model=PassageResponse,
    summary="Create Reading Passage",
    description="Create a new IELTS reading passage with questions",
    status_code=201,
    responses={
        201: {"description": "Passage created successfully"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error - invalid passage data"},
    },
)
async def create_passage(
    request: CreatePassageRequest,
    current_user=require_auth,
    controller: PassageController = Depends(get_passage_controller),
):
    """
    Create a new IELTS reading passage:

    - **title**: Descriptive title for the passage (required)
    - **content**: The main text content of the reading passage (required)
    - **questions**: List of questions related to the passage (optional)
    - **difficulty_level**: IELTS difficulty level (e.g., Academic, General) (optional)
    - **topic**: Subject category (e.g., Science, History, Environment) (optional)

    This endpoint allows creation of complete reading comprehension exercises
    with associated questions for IELTS practice tests.
    """
    return await controller.create_passage(request)


@router.get(
    "",
    response_model=list[PassageResponse],
    summary="Get All Reading Passages",
    description="Retrieve all available IELTS reading passages",
    responses={
        200: {"description": "List of passages retrieved successfully"},
        401: {"description": "Authentication required"},
    },
)
async def get_all_passages(
    current_user=require_auth,
    controller: PassageController = Depends(get_passage_controller),
):
    """
    Retrieve all available IELTS reading passages.

    Returns a complete list of reading passages including:
    - Passage metadata (ID, title, topic, difficulty)
    - Content preview
    - Associated questions count
    - Creation date

    This endpoint is useful for displaying available practice materials
    or for administrative purposes to manage the passage library.
    """
    return await controller.get_all_passages()
