from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.application.use_cases.sessions.commands.create_session.create_session_dto import (
    CreateSessionRequest,
    CreateSessionResponse,
)
from app.application.use_cases.sessions.queries.get_my_sessions.get_my_sessions_dto import (
    GetMySessionsQuery,
    GetMySessionsResponse,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_dto import (
    GetSessionByIdQuery,
    GetSessionByIdResponse,
)
from app.application.use_cases.sessions.queries.list_sessions.list_sessions_dto import (
    ListSessionsQuery,
    ListSessionsResponse,
)
from app.common.dependencies import SessionUseCases, get_session_use_cases
from app.domain.aggregates.users.user import UserRole
from app.presentation.security.dependencies import RequireRoles

router = APIRouter()


@router.post(
    "",
    response_model=CreateSessionResponse,
    summary="Create Session",
    description="""
    Create a new exercise session for a class.

    The session will be created in SCHEDULED status with all students from the class
    added as participants (initially DISCONNECTED).

    Requirements:
    - Must be an ADMIN or TEACHER
    - If TEACHER, must be teaching the specified class
    - Class must exist
    - Test must exist
    """,
    responses={
        400: {"description": "Invalid request"},
        403: {"description": "Forbidden - User does not have permission"},
        404: {"description": "Class or Test not found"},
    },
)
async def create_session(
    request: CreateSessionRequest,
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    return await use_cases.create_session_use_case.execute(
        request, user_id=current_user["user_id"]
    )


@router.get(
    "",
    response_model=ListSessionsResponse,
    summary="List Sessions",
    description="""
    List sessions with optional filters.

    Filters:
    - `teacher_id`: Get all sessions created by a specific teacher
    - `class_id`: Get all sessions for a specific class
    - No filters: Get all active sessions (WAITING_FOR_STUDENTS or IN_PROGRESS)

    Requirements:
    - Must be an ADMIN or TEACHER
    """,
)
async def list_sessions(
    teacher_id: Optional[str] = Query(
        None, description="Filter by teacher (creator) ID"
    ),
    class_id: Optional[str] = Query(None, description="Filter by class ID"),
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    query = ListSessionsQuery(teacher_id=teacher_id, class_id=class_id)
    return await use_cases.list_sessions_use_case.execute(query)


@router.get(
    "/my-sessions",
    response_model=GetMySessionsResponse,
    summary="Get My Sessions (Student)",
    description="""
    Get all sessions where the current user (student) is a participant.

    Returns sessions with student-specific information:
    - My attempt ID (if started)
    - My join time
    - My connection status

    Requirements:
    - Must be a STUDENT
    """,
)
async def get_my_sessions(
    current_user=Depends(RequireRoles([UserRole.STUDENT])),
    use_cases: SessionUseCases = Depends(get_session_use_cases),
):
    query = GetMySessionsQuery(student_id=current_user["user_id"])
    return await use_cases.get_my_sessions_use_case.execute(query)


@router.get(
    "/{session_id}",
    response_model=GetSessionByIdResponse,
    summary="Get Session by ID",
    description="""
    Get detailed information about a specific session.

    Includes:
    - Session metadata
    - All participants with their connection status
    - Attempt IDs (if session has started)

    Requirements:
    - Must be authenticated
    - Students can only see sessions they're enrolled in
    - Teachers can see sessions for their classes
    - Admins can see all sessions
    """,
)
async def get_session_by_id(
    session_id: str, use_cases: SessionUseCases = Depends(get_session_use_cases)
):
    query = GetSessionByIdQuery(session_id=session_id)
    return await use_cases.get_session_by_id_use_case.execute(query)
