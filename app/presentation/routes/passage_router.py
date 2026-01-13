from fastapi import APIRouter, Depends, status

from app.application.use_cases.passages.commands.create_complete_passage.create_complete_passage_dtos import (
    CompletePassageResponse,
    CreateCompletePassageRequest,
)
from app.application.use_cases.passages.commands.create_passage.create_passage_dtos import (
    CreatePassageRequest,
    PassageResponse,
)
from app.application.use_cases.passages.commands.update_passage.update_passage_dto import (
    UpdatePassageRequest,
)
from app.application.use_cases.passages.queries.get_passage_detail_by_id.get_passage_detail_dto import (
    GetPassageDetailByIdQuery,
    GetPassageDetailByIdResponse,
)
from app.common.dependencies import PassageUseCases, get_passage_use_cases
from app.presentation.security.dependencies import require_auth, required_admin

router = APIRouter()


@router.post(
    "/complete",
    response_model=CompletePassageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Complete Passage with Questions",
    description="Create a new complete IELTS reading passage with questions and question groups (admin only)",
    responses={
        201: {"description": "Complete passage created successfully"},
        400: {
            "description": "Invalid request - validation errors or business rule violations"
        },
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        422: {"description": "Validation error"},
    },
)
async def create_complete_passage(
    request: CreateCompletePassageRequest,
    use_cases: PassageUseCases = Depends(get_passage_use_cases),
    current_user=Depends(required_admin),
):
    """
    Create a complete IELTS reading passage with questions and question groups.

    **Admin only endpoint** - requires admin role.

    **Passage Fields:**
    - **title**: Passage title (required, 1-255 characters)
    - **content**: The reading passage text (required)
    - **difficulty_level**: Difficulty from 1-5 (default: 1)
    - **topic**: Subject category (required, e.g., "Science", "History")
    - **source**: Optional source reference

    **Question Groups (optional):**
    - Groups multiple questions with shared instructions
    - **id**: Unique identifier to link questions to the group
    - **group_instructions**: Instructions for all questions in the group
    - **question_type**: Type of questions in this group
    - **start_question_number**: First question number in range
    - **end_question_number**: Last question number in range
    - **order_in_passage**: Display order

    **Questions (required, at least 1):**
    - **question_number**: Question number in passage
    - **question_type**: Type of question (multiple_choice, true_false_not_given, etc.)
    - **question_text**: The question text
    - **options**: List of answer options (for multiple choice, matching, etc.)
    - **correct_answer**: The correct answer(s)
    - **explanation**: Optional explanation
    - **instructions**: Individual question instructions (if not in a group)
    - **points**: Points awarded (default: 1)
    - **order_in_passage**: Display order
    - **question_group_id**: Optional ID of group this belongs to

    **Business Rules:**
    - Passage must have at least one question
    - Questions in a group must match the group's question type
    - Question numbers must fall within group range if assigned to a group
    """
    return await use_cases.create_complete_passage.execute(request)


@router.post(
    "",
    response_model=PassageResponse,
    summary="Create Simple Passage (Deprecated)",
    description="Create a simple passage without questions - deprecated, use /complete instead",
    status_code=201,
    deprecated=True,
    responses={
        201: {"description": "Passage created successfully"},
        401: {"description": "Authentication required"},
        501: {"description": "Not implemented - use /complete endpoint instead"},
    },
)
async def create_passage(
    request: CreatePassageRequest,
    current_user=require_auth,
):
    """
    **DEPRECATED**: This endpoint creates passages without questions, which violates
    the domain rule that passages must have at least one question.

    Please use POST /passages/complete instead to create a complete passage with questions.
    """
    raise NotImplementedError("Create passage not yet implemented")


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
    use_cases: PassageUseCases = Depends(get_passage_use_cases),
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
    return await use_cases.get_all_passages.execute()


@router.get(
    "/{passage_id}",
    response_model=GetPassageDetailByIdResponse,
    description="Get Passage Detail by ID",
)
async def get_passage_by_id(
    passage_id: str, use_cases: PassageUseCases = Depends(get_passage_use_cases)
):
    query = GetPassageDetailByIdQuery(id=passage_id)
    return await use_cases.get_passage_detail_by_id.execute(query)


@router.put(
    "/{passage_id}",
    response_model=CompletePassageResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Passage",
    description="Update an existing passage with new data (admin only)",
    responses={
        200: {"description": "Passage updated successfully"},
        400: {
            "description": "Invalid request - validation errors or business rule violations"
        },
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        404: {"description": "Passage not found"},
        409: {
            "description": "Conflict - cannot update passage that is part of a published test"
        },
        422: {"description": "Validation error"},
    },
)
async def update_passage(
    passage_id: str,
    request: UpdatePassageRequest,
    use_cases: PassageUseCases = Depends(get_passage_use_cases),
    current_user=Depends(required_admin),
):
    """
    Update an existing IELTS reading passage with new data.

    **Admin only endpoint** - requires admin role.

    **Important constraints:**
    - Cannot update passages that are part of published tests
    - Must have exactly 13-14 questions after update
    - All validation rules from creation apply

    **Updatable Fields:**
    - Basic passage info: title, content, difficulty_level, topic, source
    - Question groups: can add, remove, modify, or reorder
    - Questions: can add, remove, modify, or reorder within groups

    **Use cases:**
    - Fix typos or errors in passage content
    - Adjust question difficulty or wording
    - Reorder questions or question groups
    - Add or remove questions (maintaining 13-14 total)
    - Update explanations or instructions

    The entire passage structure is replaced, so you must provide the complete
    updated passage with all questions and groups.
    """
    updated_passage = await use_cases.update_passage.execute(passage_id, request)
    return CompletePassageResponse.from_entity(updated_passage)
