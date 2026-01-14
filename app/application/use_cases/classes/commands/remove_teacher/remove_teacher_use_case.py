from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.application.use_cases.classes.commands.remove_teacher.remove_teacher_dto import (
    RemoveTeacherRequest,
    RemoveTeacherResponse,
)
from app.domain.aggregates.class_ import Class
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNotFoundError,
    NoPermissionToRemoveTeacherError,
    NotATeacherError,
)
from app.domain.errors.user_errors import StudentNotFoundError, UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.persistence.models import UserModel


class RemoveTeacherUseCase(
    AuthenticatedUseCase[RemoveTeacherRequest, RemoveTeacherResponse]
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
        self, request: RemoveTeacherRequest, user_id: str
    ) -> RemoveTeacherResponse:
        class_entity = await self._validate_and_fetch_class(request.class_id)

        await self._validate_user(user_id, class_entity)

        await self._validate_and_fetch_student(request.teacher_id)
        await self._validate_teacher(request.teacher_id)

        class_entity.remove_teacher(request.teacher_id)
        await self.class_repo.update(class_entity)

        new_class = await self.class_query_service.get_class_by_id(request.class_id)
        teacher_removed = request.teacher_id not in new_class.teacher_ids

        return RemoveTeacherResponse(
            class_id=new_class.id,
            teacher_id=request.teacher_id,
            teacher_removed=teacher_removed,
        )

    async def _validate_user(self, user_id: str, class_entity: Class) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToRemoveTeacherError(user_id=user_id)

        if user.role == UserRole.TEACHER and user.id not in class_entity.teacher_ids:
            raise NoPermissionToRemoveTeacherError(user_id=user_id)

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

    async def _validate_teacher(self, teacher_id: str) -> None:
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise UserNotFoundError()
        if teacher.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NotATeacherError(user_id=teacher_id)
