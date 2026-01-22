from app.application.services.query.users.user_query_model import Student, Teacher
from app.application.services.query.users.user_query_service import UserQueryService
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.application.use_cases.classes.commands.create_class.create_class_dto import (
    CreateClassRequest,
    CreateClassResponse,
    StudentDTO,
    TeacherDTO,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNameHasExisted,
    NoPermissionToCreateClassError,
    NoStudentsError,
    NoTeachersError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class CreateClassUseCase(AuthenticatedUseCase[CreateClassRequest, CreateClassResponse]):
    def __init__(
        self,
        class_repo: ClassRepositoryInterface,
        user_repo: UserRepositoryInterface,
        user_query_service: UserQueryService,
    ):
        self.class_repo = class_repo
        self.user_repo = user_repo
        self.user_query_service = user_query_service

    async def execute(
        self, request: CreateClassRequest, user_id: str
    ) -> CreateClassResponse:
        await self._validate_class_name_unique(request.name)
        creator = await self._validate_creator_permissions(user_id)
        teachers = await self._validate_and_fetch_teachers(request.teacher_ids)
        students = await self._validate_and_fetch_students(request.student_ids)
        self._ensure_creator_as_teacher(creator, request, user_id=user_id)

        new_class = Class(
            name=request.name,
            description=request.description,
            teacher_ids=[teacher.id for teacher in teachers],
            student_ids=[student.id for student in students],
            status=ClassStatus.ACTIVE,
            created_at=TimeHelper.utc_now(),
            created_by=user_id,
        )

        class_entity = await self.class_repo.create(new_class)
        teacher_dtos = self._convert_teachers_to_dtos(teachers)
        student_dtos = self._convert_students_to_dtos(students)

        return CreateClassResponse(
            id=class_entity.id,
            name=class_entity.name,
            description=class_entity.description,
            created_at=class_entity.created_at,
            status=class_entity.status,
            teachers=teacher_dtos,
            students=student_dtos,
        )

    async def _validate_class_name_unique(self, name: str) -> None:
        """Validate that the class name is not already in use."""
        existing_classname = await self.class_repo.is_class_name_already_used(name)
        if existing_classname:
            raise ClassNameHasExisted(class_name=name)

    async def _validate_creator_permissions(self, created_by: str):
        """Validate that the creator exists and has permission to create classes."""
        creator = await self.user_repo.get_by_id(created_by)
        if not creator:
            raise UserNotFoundError(created_by)
        if creator.role not in [UserRole.ADMIN, UserRole.TEACHER]:
            raise NoPermissionToCreateClassError(user_id=created_by)
        return creator

    async def _validate_and_fetch_teachers(
        self, teacher_ids: list[str] | None
    ) -> list[Teacher]:
        """Validate and fetch teachers by IDs."""
        teachers: list[Teacher] = []
        if teacher_ids:
            teachers = await self.user_query_service.get_teachers_by_ids(teacher_ids)
            if not teachers:
                raise NoTeachersError(teacher_ids)
        return teachers

    async def _validate_and_fetch_students(
        self, student_ids: list[str] | None
    ) -> list[Student]:
        """Validate that all student IDs belong to users with a STUDENT role."""
        students: list[Student] = []
        if student_ids:
            students = await self.user_query_service.get_students_by_ids(student_ids)
            if not students:
                raise NoStudentsError(student_ids)
        return students

    def _ensure_creator_as_teacher(
        self, creator, request: CreateClassRequest, user_id: str
    ) -> None:
        """Ensure that if the creator is a teacher, they are added to the teacher list."""
        if request.teacher_ids is None:
            return
        if creator.role == UserRole.TEACHER and user_id not in request.teacher_ids:
            request.teacher_ids.append(user_id)

    def _convert_teachers_to_dtos(self, teachers: list[Teacher]) -> list[TeacherDTO]:
        """Convert teacher domain models to DTOs."""
        return [
            TeacherDTO(
                id=teacher.id,
                username=teacher.username,
                full_name=teacher.full_name,
                email=teacher.email,
            )
            for teacher in teachers
        ]

    def _convert_students_to_dtos(self, students: list[Student]) -> list[StudentDTO]:
        return [
            StudentDTO(
                id=student.id,
                username=student.username,
                full_name=student.full_name,
                email=student.email,
            )
            for student in students
        ]
