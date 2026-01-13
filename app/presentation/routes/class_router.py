from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.application.services.query.classes.class_query_model import ClassSortField
from app.application.use_cases.classes.commands.create_class.create_class_dto import (
    CreateClassRequest,
    CreateClassResponse,
)
from app.application.use_cases.classes.commands.enroll_student.enroll_student_dto import (
    EnrollStudentRequest,
    EnrollStudentResponse,
)
from app.application.use_cases.classes.queries.get_class_by_id.get_class_by_id_dto import (
    GetClassByIdQuery,
    GetClassByIdResponse,
)
from app.application.use_cases.classes.queries.list_classes.list_classes_dto import (
    ListClassesQuery,
    ListClassesResponse,
)
from app.common.dependencies import ClassUseCases, get_class_use_cases
from app.common.pagination import SortOrder
from app.domain.aggregates.users.user import UserRole
from app.presentation.security.dependencies import RequireRoles

router = APIRouter()


@router.get(
    "",
    response_model=ListClassesResponse,
    summary="List Classes",
    description="""
    Retrieve classes with pagination, sorting, and filtering options.

    Filters:
    - `teacher_id`: Filter classes taught by a specific teacher
    - `name`: Search classes by name (case-insensitive partial match)

    Sorting:
    - `sort_by`: Field to sort by (name, created_at, created_by, status)
    - `sort_order`: Sort direction (asc or desc)

    Pagination:
    - `page`: Page number (1-indexed)
    - `page_size`: Number of items per page (max 100)
    """,
)
async def list_classes(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: ClassSortField = Query(
        ClassSortField.CREATED_AT, description="Field to sort by"
    ),
    sort_order: SortOrder = Query(
        SortOrder.DESC, description="Sort order (asc or desc)"
    ),
    name: Optional[str] = Query(
        None, description="Filter by class name (partial match)"
    ),
    teacher_id: Optional[str] = Query(None, description="Filter by teacher ID"),
    use_cases: ClassUseCases = Depends(get_class_use_cases),
):
    query = ListClassesQuery(
        teacher_id=teacher_id,
        name=name,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return await use_cases.list_classes_use_case.execute(query)


@router.get(
    "/{class_id}",
    response_model=GetClassByIdResponse,
    summary="Get Class by ID",
)
async def get_class_by_id(
    class_id: str, use_cases: ClassUseCases = Depends(get_class_use_cases)
):
    query = GetClassByIdQuery(id=class_id)
    return await use_cases.get_class_by_id_use_case.execute(query)


@router.post(
    "",
    response_model=CreateClassResponse,
    summary="Create Class",
    description="Create a new class",
)
async def create_class(
    request: CreateClassRequest,
    current_user=Depends(RequireRoles([UserRole.ADMIN])),
    use_cases: ClassUseCases = Depends(get_class_use_cases),
):
    create_class_request = CreateClassRequest(
        name=request.name,
        description=request.description,
        teacher_ids=request.teacher_ids,
        student_ids=request.student_ids,
    )

    return await use_cases.create_class_use_case.execute(
        create_class_request, user_id=current_user["user_id"]
    )


class EnrollRequest(BaseModel):
    student_id: str


@router.post(
    "{class_id}/enroll",
    response_model=EnrollStudentResponse,
    summary="Enroll Student in Class",
    description="""
    Enroll a student in a class.
    The creator must be either an ADMIN or a teacher.
    If he is a teacher, he must be in the list of teachers who are teaching that class
    """,
    responses={
        400: {"description": "Invalid request"},
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        403: {"description": "Forbidden"},
    },
)
async def enroll_student(
    class_id: str,
    request: EnrollRequest,
    current_user=Depends(RequireRoles([UserRole.ADMIN, UserRole.TEACHER])),
    use_cases: ClassUseCases = Depends(get_class_use_cases),
):
    command = EnrollStudentRequest(class_id=class_id, student_id=request.student_id)
    return await use_cases.enroll_student_use_case.execute(
        request=command, user_id=current_user["user_id"]
    )
