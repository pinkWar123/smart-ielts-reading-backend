from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
    RequestType,
    ResponseType,
)
from app.application.use_cases.classes.commands.remove_student.remove_student_dto import (
    RemoveStudentRequest,
    RemoveStudentResponse,
)
from app.domain.aggregates.class_ import Class
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNotFoundError,
    NoPermissionToRemoveStudentError,
)
from app.domain.errors.user_errors import StudentNotFoundError, UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.persistence.models import UserModel


class RemoveStudentUseCase(
    AuthenticatedUseCase[RemoveStudentRequest, RemoveStudentResponse]
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
        self, request: RemoveStudentRequest, user_id: str
    ) -> RemoveStudentResponse:
        class_entity = await self._validate_and_fetch_class(request.class_id)

        await self._validate_user(user_id, class_entity)

        await self._validate_and_fetch_student(request.student_id)

        class_entity.remove_student(request.student_id)
        await self.class_repo.update(class_entity)

        new_class = await self.class_query_service.get_class_by_id(request.class_id)
        students = new_class.students

        return RemoveStudentResponse(
            class_id=new_class.id,
            student_id=request.student_id,
            student_removed=True,
            students=students,
        )

    async def _validate_user(self, user_id: str, class_entity: Class) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToRemoveStudentError(user_id=user_id)

        if user.role == UserRole.TEACHER and user.id not in class_entity.teacher_ids:
            raise NoPermissionToRemoveStudentError(user_id=user_id)

    async def _validate_and_fetch_student(self, student_id: str) -> UserModel:
        student_model = await self.user_repo.get_by_id(student_id)

        if not student_model or student_model.role != UserRole.STUDENT:
            raise StudentNotFoundError()

        return student_model

    async def _validate_and_fetch_class(self, class_id: str) -> Class:
        class_model = await self.class_query_service.get_class_by_id(class_id)

        if not class_model:
            raise ClassNotFoundError(class_id=class_id)

        return class_model.to_domain()
