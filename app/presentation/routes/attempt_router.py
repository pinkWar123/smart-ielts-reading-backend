from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_dto import (
    RecordHighlightResponse,
)
from app.application.use_cases.attempts.commands.progress.record_violation.record_violation_dto import (
    RecordViolationResponse,
)
from app.application.use_cases.attempts.commands.progress.update_answer.update_answer_dto import (
    UpdateAnswerRequest,
    UpdateAnswerResponse,
)
from app.application.use_cases.attempts.commands.progress.update_progress.update_progress_dto import (
    UpdateProgressRequest,
    UpdateProgressResponse,
)
from app.application.use_cases.attempts.commands.submit.submit_attempt_dto import (
    SubmitAttemptRequest,
    SubmitAttemptResponse,
)
from app.application.use_cases.attempts.queries.get_by_id.get_by_id_dto import (
    GetAttemptByIdQuery,
    GetAttemptByIdResponse,
)
from app.common.dependencies import AttemptUseCases, get_attempt_use_cases
from app.domain.aggregates.attempt.attempt import SubmitType
from app.domain.aggregates.attempt.violation_type import ViolationType
from app.domain.aggregates.users.user import UserRole
from app.presentation.security.dependencies import RequireRoles

router = APIRouter()


@router.get(
    "/{attempt_id}",
    response_model=GetAttemptByIdResponse,
    description="""
    Get attempt by ID
    Retrieve current attempt state (for reconnection/state sync)
    Authentication:
    - JWT token in Authorization header
    - Roles: STUDENT (own attempts), TEACHER(class sessions), ADMIN
    
    Rules:
    - Students can only access their own attempts
    - Teachers can access attempts of students in their classes
    - Admins can access any attempt
    """,
    responses={
        200: {"description": "Attempt retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "User doesn't have permission to view this attempt"},
        404: {"description": "Attempt not found"},
    },
)
async def get_attempt_by_id(
    attempt_id: str,
    current_user=Depends(
        RequireRoles([UserRole.STUDENT, UserRole.TEACHER, UserRole.ADMIN])
    ),
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
):
    query = GetAttemptByIdQuery(id=attempt_id)
    return await use_cases.get_attempt_by_id.execute(
        query, user_id=current_user["user_id"]
    )


class UpdateAnswerContract(BaseModel):
    answer: str
    question_id: str


@router.post("/{attempt_id}/answers", response_model=UpdateAnswerResponse)
async def update_answer(
    attempt_id: str,
    request: UpdateAnswerContract,
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
):
    use_case_request = UpdateAnswerRequest(
        attempt_id=attempt_id, question_id=request.question_id, answer=request.answer
    )
    return await use_cases.update_answer.execute(
        use_case_request, user_id=current_user["user_id"]
    )


class UpdateProgressContract(BaseModel):
    passage_index: int
    question_index: int
    passage_id: str | None = None
    question_id: str | None = None


@router.post(
    "/{attempt_id}/progress",
    response_model=UpdateProgressResponse,
    description="""
    Update student's progress in the test

    Business rules:
    - Only students can update their own attempt progress
    - Attempt must be IN_PROGRESS status
    - Progress is immediately persisted to database
    - Client should debounce progress updates (e.g., max 1 update per 2 seconds)
    """,
    responses={
        200: {"description": "Progress updated successfully"},
        400: {"description": "Invalid progress data"},
        401: {"description": "Authentication required"},
        403: {"description": "User doesn't have permission"},
        404: {"description": "Attempt not found"},
    },
)
async def update_progress(
    attempt_id: str,
    request: UpdateProgressContract,
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
):
    use_case_request = UpdateProgressRequest(
        attempt_id=attempt_id,
        passage_index=request.passage_index,
        question_index=request.question_index,
        passage_id=request.passage_id,
        question_id=request.question_id,
    )
    return await use_cases.update_progress.execute(
        use_case_request, user_id=current_user["user_id"]
    )


class RecordHighlightContract(BaseModel):
    text: str
    passage_id: str
    position_start: int
    position_end: int
    color: str | None = "yellow"


@router.post(
    "/{attempt_id}/highlights",
    response_model=RecordHighlightResponse,
    status_code=201,
    description="""
    Record text highlighted by student during test

    Business rules:
    - Only students can record highlights in their own attempts
    - Attempt must be IN_PROGRESS status
    - Highlights are saved immediately to database
    - Students can have multiple overlapping highlights
    - Maximum 100 highlights per attempt
    """,
    responses={
        201: {"description": "Highlight saved successfully"},
        400: {"description": "Invalid highlight data"},
        401: {"description": "Authentication required"},
        403: {"description": "User doesn't have permission"},
        404: {"description": "Attempt or passage not found"},
    },
)
async def record_highlight(
    attempt_id: str,
    request: RecordHighlightContract,
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
):
    from app.application.use_cases.attempts.commands.progress.record_highlight.record_highlight_dto import (
        RecordHighlightRequest,
    )

    use_case_request = RecordHighlightRequest(
        attempt_id=attempt_id,
        text=request.text,
        passage_id=request.passage_id,
        position_start=request.position_start,
        position_end=request.position_end,
        color=request.color,
    )
    return await use_cases.record_highlight.execute(
        use_case_request, user_id=current_user["user_id"]
    )


class RecordViolationContract(BaseModel):
    violation_type: ViolationType
    metadata: dict[str, str] | None = None


@router.post(
    "/{attempt_id}/violations",
    response_model=RecordViolationResponse,
    status_code=201,
    description="""
    Record tab switches and other violations during test

    Business rules:
    - Only students can record violations in their own attempts
    - Attempt must be IN_PROGRESS status
    - Violations are recorded immediately
    - Broadcast to teacher via WebSocket if part of a session
    - Rate limiting: max 1 violation per second per type (prevent spam)
    """,
    responses={
        201: {"description": "Violation recorded successfully"},
        400: {"description": "Invalid violation data"},
        401: {"description": "Authentication required"},
        403: {"description": "User doesn't have permission"},
        404: {"description": "Attempt not found"},
    },
)
async def record_violation(
    attempt_id: str,
    request: RecordViolationContract,
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
):
    from app.application.use_cases.attempts.commands.progress.record_violation.record_violation_dto import (
        RecordViolationRequest,
    )

    use_case_request = RecordViolationRequest(
        attempt_id=attempt_id,
        violation_type=request.violation_type,
        metadata=request.metadata,
    )
    return await use_cases.record_violation.execute(
        use_case_request, user_id=current_user["user_id"]
    )


class SubmitAttemptContract(BaseModel):
    submit_type: SubmitType

    class Config:
        use_enum_values = True


@router.post(
    "/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
    status_code=201,
    description="""
    Submit attempt and calculate score
    """,
    responses={
        201: {"description": "Attempt submitted successfully"},
        400: {"description": "Invalid submission data"},
        401: {"description": "Authentication required"},
        403: {"description": "User doesn't have permission"},
        404: {"description": "Attempt not found"},
    },
)
async def submit_attempt(
    attempt_id: str,
    request: SubmitAttemptContract,
    use_cases: AttemptUseCases = Depends(get_attempt_use_cases),
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
):
    use_case_request = SubmitAttemptRequest(
        attempt_id=attempt_id, submit_type=request.submit_type
    )
    return await use_cases.submit_attempt.execute(
        use_case_request, user_id=current_user["user_id"]
    )
