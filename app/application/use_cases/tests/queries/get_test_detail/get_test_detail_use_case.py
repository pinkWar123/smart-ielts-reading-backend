from app.application.services.query.tests.test_query_model import AuthorInfo
from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.queries.get_test_detail.get_test_detail_dto import (
    GetTestDetailQuery,
    GetTestDetailResponse,
    PassageDTO,
    TestMetadata,
    UserInfo,
)


class GetTestDetailUseCase(UseCase[GetTestDetailQuery, GetTestDetailResponse]):
    def __init__(self, test_query_service: TestQueryService):
        self.test_query_service = test_query_service

    async def execute(self, request: GetTestDetailQuery) -> GetTestDetailResponse:
        test_model = await self.test_query_service.get_test_by_id_with_details(
            request.id
        )

        metadata = TestMetadata(
            title=test_model.title,
            description=test_model.description,
            total_questions=test_model.total_questions,
            estimated_time_minutes=test_model.time_limit_minutes,
            type=test_model.test_type,
            status=test_model.status,
            created_by=self._convert_to_user_info(test_model.created_by),
            created_at=str(test_model.created_at),
            updated_at=str(test_model.updated_at),
        )
        response = GetTestDetailResponse(
            test_metadata=metadata,
            passages=(
                [
                    PassageDTO.convert_to_dto(passage, request.view)
                    for passage in test_model.passages
                ]
                if test_model.passages
                else []
            ),
        )

        return response

    @staticmethod
    def _convert_to_user_info(author_info: AuthorInfo) -> UserInfo:
        return UserInfo(
            id=author_info.id,
            name=author_info.full_name,
            email=author_info.email,
        )
