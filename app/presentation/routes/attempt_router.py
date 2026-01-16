from fastapi import APIRouter, Depends

from app.application.use_cases.attempts.queries.get_by_id.get_by_id_dto import (
    GetAttemptByIdQuery,
    GetAttemptByIdResponse,
)
from app.common.dependencies import AttemptUseCases, get_attempt_use_cases
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
