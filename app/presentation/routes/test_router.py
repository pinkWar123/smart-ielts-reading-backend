from dependency_injector.wiring import Provide
from fastapi import APIRouter, status
from fastapi.params import Depends

from app.application.use_cases.tests.create_test.create_test_dtos import (
    AddPassageToTestRequest,
    CreateTestRequest,
    TestResponse,
)
from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.test_controller import TestController
from app.presentation.security.dependencies import required_admin

router = APIRouter()

get_test_controller = make_service_dependency(
    Provide[ApplicationContainer.test_controller]
)


@router.post(
    "",
    response_model=TestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Empty Test",
    description="Create a new empty test (admin only)",
    responses={
        201: {"description": "Test created successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"},
    },
)
async def create_test(
    request: CreateTestRequest,
    controller: TestController = Depends(get_test_controller),
    current_user=Depends(required_admin),
):
    """
    Create a new empty test.

    **Admin only endpoint** - requires admin role.

    - **title**: Test title (required, 1-255 characters)
    - **description**: Test description (optional)
    - **test_type**: Type of test - FULL_TEST (3 passages) or SINGLE_PASSAGE (1 passage)
    - **time_limit_minutes**: Time limit in minutes (required, >= 1)

    The test is created with status DRAFT and can have passages added to it.
    Total questions and points are initially 0 and will be updated as passages are added.
    """
    return await controller.create_test(request, current_user.id)


@router.post(
    "/{test_id}/passages",
    response_model=TestResponse,
    summary="Add Passage to Test",
    description="Add a complete passage to an existing test (admin only)",
    responses={
        200: {"description": "Passage added successfully"},
        400: {
            "description": "Invalid request - test not found, passage not found, or business rule violation"
        },
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"},
    },
)
async def add_passage_to_test(
    test_id: str,
    request: AddPassageToTestRequest,
    controller: TestController = Depends(get_test_controller),
    current_user=Depends(required_admin),
):
    """
    Add a complete passage to an existing test.

    **Admin only endpoint** - requires admin role.

    - **test_id**: ID of the test to add passage to (path parameter)
    - **passage_id**: ID of the passage to add (required in request body)

    Business rules enforced:
    - Cannot add passages to published tests
    - FULL_TEST can have maximum 3 passages
    - SINGLE_PASSAGE can have maximum 1 passage
    - Passage cannot be added twice to the same test
    - Passage must exist in the database

    The test's total_questions and total_points are automatically updated based on the passage.
    """
    return await controller.add_passage_to_test(test_id, request)
