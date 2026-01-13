from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.classes.queries.get_class_by_id.get_class_by_id_dto import (
    GetClassByIdQuery,
    GetClassByIdResponse,
)
from app.domain.errors.class_errors import ClassNotFoundError


class GetClassByIdUseCase(UseCase[GetClassByIdQuery, GetClassByIdResponse]):
    def __init__(self, class_query_service: ClassQueryService):
        self.class_query_service = class_query_service

    async def execute(self, request: GetClassByIdQuery) -> GetClassByIdResponse:
        class_detail = await self.class_query_service.get_class_by_id(request.id)
        if class_detail is None:
            raise ClassNotFoundError(class_id=request.id)

        return GetClassByIdResponse(
            id=class_detail.id,
            name=class_detail.name,
            description=class_detail.description,
            status=class_detail.status,
            created_at=class_detail.created_at,
            created_by=class_detail.created_by,
            students=class_detail.students,
            teachers=class_detail.teachers,
        )
