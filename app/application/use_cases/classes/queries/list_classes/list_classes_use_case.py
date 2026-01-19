from app.application.services.query.classes.class_query_service import ClassQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.classes.queries.list_classes.list_classes_dto import (
    ClassCreatorDTO,
    ClassDTO,
    ListClassesQuery,
    ListClassesResponse,
)


class ListClassesUseCase(UseCase[ListClassesQuery, ListClassesResponse]):
    def __init__(self, class_query_service: ClassQueryService):
        self.class_query_service = class_query_service

    async def execute(self, request: ListClassesQuery) -> ListClassesResponse:
        response = await self.class_query_service.list_classes(
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            teacher_id=request.teacher_id,
            name=request.name,
        )

        if response.data is not None and len(response.data) > 0:
            print("Logging to see whether class model has id or not")
            print(response.data)

        class_dtos = [
            ClassDTO(
                id=class_model["id"],
                name=class_model["name"],
                students_count=len(class_model["users"]),
                description=class_model["description"],
                status=class_model["status"],
                created_at=class_model["created_at"],
                created_by=ClassCreatorDTO(
                    id=class_model["created_by"].id,
                    username=class_model["created_by"].username,
                ),
            )
            for class_model in response.data
        ]

        return ListClassesResponse(data=class_dtos, meta=response.meta)
