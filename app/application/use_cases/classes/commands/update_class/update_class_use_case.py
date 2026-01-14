from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import AuthenticatedUseCase
from app.application.use_cases.classes.commands.update_class.update_class_dto import (
    UpdateClassRequest,
    UpdateClassResponse,
)
from app.domain.aggregates.users.user import UserRole
from app.domain.errors.class_errors import (
    ClassNotFoundError,
    NoPermissionToUpdateClassError,
)
from app.domain.errors.user_errors import UserNotFoundError
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class UpdateClassUseCase(AuthenticatedUseCase[UpdateClassRequest, UpdateClassResponse]):
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
        self, request: UpdateClassRequest, user_id: str
    ) -> UpdateClassResponse:
        # Fetch the class
        class_model = await self.class_query_service.get_class_by_id(request.class_id)
        if not class_model:
            raise ClassNotFoundError(class_id=request.class_id)

        class_entity = class_model.to_domain()

        # Fetch the user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()

        # Check permissions: must be ADMIN or a TEACHER in the class
        if user.role not in [UserRole.TEACHER, UserRole.ADMIN]:
            raise NoPermissionToUpdateClassError(
                user_id=user_id, class_id=request.class_id
            )

        if user.role == UserRole.TEACHER and user.id not in class_entity.teacher_ids:
            raise NoPermissionToUpdateClassError(
                user_id=user_id, class_id=request.class_id
            )

        # Update class details
        class_entity.update_details(
            name=request.name,
            description=request.description,
            status=request.status,
        )

        # Save to repository
        updated_class = await self.class_repo.update(class_entity)

        return UpdateClassResponse(
            id=updated_class.id,
            name=updated_class.name,
            description=updated_class.description,
            status=updated_class.status,
            updated_at=updated_class.updated_at,
        )
