from app.application.services.query.tests.test_query_service import TestQueryService
from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.tests.commands.publish_test.publish_test_dto import (
    PassageDTO,
    PublishTestRequest,
    PublishTestResponse,
)
from app.domain.aggregates.passage import Passage
from app.domain.aggregates.test import TestType
from app.domain.aggregates.test.constants import (
    FULL_TEST_QUESTIONS_COUNT,
    SINGLE_PASSAGE_MAX_QUESTIONS_COUNT,
    SINGLE_PASSAGE_MIN_QUESTIONS_COUNT,
)
from app.domain.errors.test_errors import (
    InvalidFullTestQuestionCountError,
    InvalidSinglePassageQuestionCountError,
    TestNotFoundError,
)
from app.domain.repositories.test_repository import TestRepositoryInterface


class PublishTestUseCase(UseCase[PublishTestRequest, PublishTestResponse]):
    def __init__(
        self,
        test_query_service: TestQueryService,
        test_repository: TestRepositoryInterface,
    ):
        self.test_query_service = test_query_service
        self.test_repository = test_repository

    async def execute(self, request: PublishTestRequest) -> PublishTestResponse:
        test_query_model = await self.test_query_service.get_test_by_id_with_details(
            test_id=request.id
        )

        if not test_query_model:
            raise TestNotFoundError(request.id)

        question_count = sum(
            [passage.get_total_questions() for passage in test_query_model.passages]
        )
        self._validate_question_count(test_query_model.test_type, question_count)

        test = test_query_model.to_domain_entity()
        test.publish()
        await self.test_repository.update(test)

        return PublishTestResponse(
            id=test.id,
            title=test.title,
            description=test.description,
            test_type=test.test_type,
            passage_ids=test.passage_ids,
            time_limit_minutes=test.time_limit_minutes,
            total_questions=test.total_questions,
            total_points=test.total_points,
            status=test.status,
            created_by=test_query_model.created_by.full_name,
            created_at=test.created_at,
            updated_at=test.updated_at,
            is_active=test.is_active,
            passages=[
                self._to_passage_dto(passage) for passage in test_query_model.passages
            ],
        )

    def _validate_question_count(
        self, test_type: TestType, question_count: int
    ) -> None:
        if test_type == TestType.FULL_TEST:
            if question_count != FULL_TEST_QUESTIONS_COUNT:
                raise InvalidFullTestQuestionCountError(
                    expected=FULL_TEST_QUESTIONS_COUNT, actual=question_count
                )

        if test_type == TestType.SINGLE_PASSAGE:
            if question_count not in [
                SINGLE_PASSAGE_MIN_QUESTIONS_COUNT,
                SINGLE_PASSAGE_MAX_QUESTIONS_COUNT,
            ]:
                raise InvalidSinglePassageQuestionCountError(
                    min_q=SINGLE_PASSAGE_MIN_QUESTIONS_COUNT,
                    max_q=SINGLE_PASSAGE_MAX_QUESTIONS_COUNT,
                    actual=question_count,
                )

    def _to_passage_dto(self, passage: Passage) -> PassageDTO:
        return PassageDTO(
            id=passage.id,
            title=passage.title,
            reduced_content=passage.get_reduced_content(),
            word_count=passage.word_count,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            created_by=passage.created_by,
            created_at=passage.created_at,
        )
