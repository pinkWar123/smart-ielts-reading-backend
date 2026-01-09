from typing import List, Optional

from fastapi import APIRouter, Query, status
from fastapi.params import Depends

from app.application.use_cases.common.dtos.passage_detail_dto import UserView
from app.application.use_cases.passages.commands.delete_passage_by_id.delete_passage_by_id_dto import (
    DeletePassageByIdRequest,
)
from app.application.use_cases.tests.commands.create_test.create_test_dtos import (
    AddPassageToTestRequest,
    CreateTestRequest,
    TestResponse,
)
from app.application.use_cases.tests.commands.publish_test.publish_test_dto import (
    PublishTestRequest,
)
from app.application.use_cases.tests.queries.get_all_tests.get_all_tests_dto import (
    GetAllTestsQueryParams,
    GetAllTestsResponse,
)
from app.application.use_cases.tests.queries.get_paginated_full_tests.get_paginated_full_tests_dto import (
    GetPaginatedFullTestsQuery,
    GetPaginatedFullTestsResponse,
)
from app.application.use_cases.tests.queries.get_paginated_single_tests.get_paginated_single_tests_dto import (
    GetPaginatedSingleTestsQuery,
    GetPaginatedSingleTestsResponse,
)
from app.application.use_cases.tests.queries.get_test_detail.get_test_detail_dto import (
    GetTestDetailQuery,
    GetTestDetailResponse,
)
from app.application.use_cases.tests.queries.get_test_with_passages.get_test_with_passages_dto import (
    GetTestWithPassagesQuery,
    GetTestWithPassagesResponse,
)
from app.common.dependencies import TestUseCases, get_test_use_cases
from app.domain.aggregates.passage import QuestionType
from app.domain.aggregates.test import TestStatus, TestType
from app.presentation.security.dependencies import required_admin

router = APIRouter()


@router.get(
    "",
    response_model=GetAllTestsResponse,
    summary="Get All Tests",
    description="Retrieve all tests (admin only)",
    responses={
        200: {"description": "List of tests retrieved successfully"},
        # 401: {"description": "Authentication required"},
        # 403: {"description": "Admin access required"},
    },
)
async def get_all_tests(
    test_status: Optional[TestStatus] = None,
    test_type: Optional[TestType] = None,
    use_cases: TestUseCases = Depends(get_test_use_cases),
    # current_user=Depends(required_admin),
):
    query = GetAllTestsQueryParams(status=test_status, type=test_type)
    return await use_cases.get_all_tests.execute(query)


@router.get(
    "/single-tests",
    response_model=GetPaginatedSingleTestsResponse,
    summary="Get single tests with filters and pagination",
    description="Retrieve paginated single tests with filters",
)
async def get_paginated_single_tests(
    page: int = 1,
    page_size: int = 10,
    question_types: Optional[List[QuestionType]] = Query(None),
    use_cases: TestUseCases = Depends(get_test_use_cases),
):
    query = GetPaginatedSingleTestsQuery(
        page=page, page_size=page_size, question_types=question_types
    )
    return await use_cases.get_paginated_single_tests.execute(query)


@router.get(
    "/full-tests",
    response_model=GetPaginatedFullTestsResponse,
    summary="Get full tests with pagination",
    description="Retrieve paginated full tests with pagination",
)
async def get_paginated_full_tests(
    page: int = 1,
    page_size: int = 10,
    use_cases: TestUseCases = Depends(get_test_use_cases),
):
    query = GetPaginatedFullTestsQuery(page=page, page_size=page_size)
    return await use_cases.get_paginated_full_tests.execute(query)


@router.get(
    "/{test_id}", response_model=GetTestWithPassagesResponse, summary="Get Test by ID"
)
async def get_test_by_id(
    test_id: str, use_cases: TestUseCases = Depends(get_test_use_cases)
):
    query = GetTestWithPassagesQuery(id=test_id)
    return await use_cases.get_test_by_id.execute(query)


@router.get(
    "/{test_id}/detail",
    response_model=GetTestDetailResponse,
    summary="Get test with passages, question groups and questions by ID",
)
async def get_test_detail(
    test_id: str, view: UserView, use_cases: TestUseCases = Depends(get_test_use_cases)
):
    query = GetTestDetailQuery(id=test_id, view=view)
    return await use_cases.get_test_detail_by_id.execute(query)


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
    use_cases: TestUseCases = Depends(get_test_use_cases),
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
    return await use_cases.create_test.execute(request, current_user["user_id"])


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
    use_cases: TestUseCases = Depends(get_test_use_cases),
    # current_user=Depends(required_admin),
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
    return await use_cases.add_passage_to_test.execute(test_id, request)


@router.post(
    "/{test_id}/publish",
    response_model=TestResponse,
    summary="Publish a test",
    description="Publish a test after validating business rules (admin only). After this action, the test becomes immutable and cannot be modified."
    "Normal user can see this test",
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
async def publish_test(
    test_id: str,
    use_cases: TestUseCases = Depends(get_test_use_cases),
):
    request = PublishTestRequest(id=test_id)
    return await use_cases.publish_test.execute(request)


@router.delete(
    "/{test_id}/passages/{passage_id}",
    summary="Delete Test",
    description="Remove a passage from a test",
)
async def remove_passage_from_test(
    test_id: str,
    passage_id: str,
    use_cases: TestUseCases = Depends(get_test_use_cases),
):
    request = DeletePassageByIdRequest(test_id=test_id, passage_id=passage_id)
    return await use_cases.remove_passage_use_case.execute(request)
