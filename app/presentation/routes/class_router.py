from fastapi import APIRouter, Depends

from app.application.use_cases.classes.commands.create_class.create_class_dto import (
    CreateClassRequest,
    CreateClassResponse,
)
from app.common.dependencies import ClassUseCases, get_class_use_cases
from app.domain.aggregates.users.user import UserRole
from app.presentation.security.dependencies import RequireRoles

router = APIRouter()


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

    print(current_user)

    return await use_cases.create_class_use_case.execute(
        create_class_request, user_id=current_user["user_id"]
    )
