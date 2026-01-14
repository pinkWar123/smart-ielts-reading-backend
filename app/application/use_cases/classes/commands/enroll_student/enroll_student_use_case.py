from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.application.use_cases.classes.commands.enroll_student.enroll_student_dto import (
    EnrollStudentRequest,
    EnrollStudentResponse,
)
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNotFoundError,
    NoPermissionToAddStudentError,
    NotAStudent,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class EnrollStudentUseCase(
    AuthenticatedUseCase[EnrollStudentRequest, EnrollStudentResponse]
):
    def __init__(
        self,
        class_query_service: ClassQueryService,
        class_repo: ClassRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.class_query_service = class_query_service
        self.class_repo = class_repo
        self.user_repo = user_repo

    async def execute(
        self, request: EnrollStudentRequest, user_id: str
    ) -> EnrollStudentResponse:
        class_model = await self.class_query_service.get_class_by_id(request.class_id)
        if not class_model:
            raise ClassNotFoundError(class_id=request.class_id)

        class_entity = class_model.to_domain()
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToAddStudentError(user_id=user_id)

        if user.role == UserRole.TEACHER and user.id not in class_entity.teacher_ids:
            raise NoPermissionToAddStudentError(user_id=user_id)

        student = await self.user_repo.get_by_id(request.student_id)
        if not student or student.role != UserRole.STUDENT:
            raise NotAStudent(user_id=request.student_id)

        class_entity.enroll_student(request.student_id)

        updated_class = await self.class_repo.update(class_entity)

        return EnrollStudentResponse(
            student_id=request.student_id, enrollment_date=updated_class.updated_at
        )
