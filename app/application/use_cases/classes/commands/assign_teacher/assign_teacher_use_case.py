from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
)
from app.application.use_cases.classes.commands.assign_teacher.assign_teacher_dto import (
    AssignTeacherRequest,
    AssignTeacherResponse,
)
from app.domain.aggregates.class_ import Class
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNotFoundError,
    NoPermissionToAssignTeacherToClass,
    NoPermissionToAssignTeacherToClassThatYouDontTeach,
    NotATeacherError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class AssignTeacherUseCase(
    AuthenticatedUseCase[AssignTeacherRequest, AssignTeacherResponse]
):
    def __init__(
        self,
        class_repo: ClassRepositoryInterface,
        class_query_service: ClassQueryService,
        user_repo: UserRepositoryInterface,
    ):
        self.class_repo = class_repo
        self.class_query_service = class_query_service
        self.user_repo = user_repo

    async def execute(
        self, request: AssignTeacherRequest, user_id: str
    ) -> AssignTeacherResponse:
        class_entity = await self._validate_and_fetch_class(request.class_id)
        await self._validate_user(
            user_id=user_id, teacher_id=request.teacher_id, class_entity=class_entity
        )
        await self._validate_teacher(request.teacher_id)

        class_entity.assign_teacher(teacher_id=request.teacher_id)
        await self.class_repo.update(class_entity)

        new_class = await self._validate_and_fetch_class(request.class_id)
        teacher_assigned = request.teacher_id in new_class.teacher_ids

        return AssignTeacherResponse(
            class_id=new_class.id,
            teacher_id=request.teacher_id,
            teacher_assigned=teacher_assigned,
        )

    async def _validate_and_fetch_class(self, class_id: str) -> Class:
        class_model = await self.class_query_service.get_class_by_id(class_id)
        if not class_model:
            raise ClassNotFoundError(class_id=class_id)

        return class_model.to_domain()

    async def _validate_user(
        self, user_id: str, teacher_id: str, class_entity: Class
    ) -> None:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToAssignTeacherToClass(
                user_id=user_id, class_id=class_entity.id
            )

        # If a user is an admin, he can assign any teacher to any class
        # If a user is a teacher, he can only assign other teachers to his classes
        if (
            user.role == UserRole.TEACHER
            and user.id != teacher_id
            and user.id not in class_entity.teacher_ids
        ):
            raise NoPermissionToAssignTeacherToClassThatYouDontTeach(
                user_id=user_id, class_id=class_entity.id
            )

    async def _validate_teacher(self, teacher_id: str) -> None:
        teacher = await self.user_repo.get_by_id(teacher_id)
        if not teacher:
            raise UserNotFoundError()
        if teacher.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NotATeacherError(user_id=teacher_id)
