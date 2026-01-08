"""SQL implementation of Test Query Service

This implementation uses optimized SQL queries with JOINs to fetch test data
with author information in a single database round-trip.
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.services.query.tests.test_query_model import (
    AuthorInfo,
    TestWithAuthorQueryModel,
    TestWithDetailsQueryModel,
    TestWithPassagesQueryModel,
)
from app.application.services.query.tests.test_query_service import TestQueryService
from app.domain.aggregates.passage import Passage
from app.domain.aggregates.passage.question import Question, QuestionType
from app.domain.aggregates.passage.question_group import QuestionGroup
from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType
from app.domain.errors.test_errors import TestNotFoundError
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option
from app.infrastructure.persistence.models import QuestionGroupModel
from app.infrastructure.persistence.models.passage_model import PassageModel
from app.infrastructure.persistence.models.test_model import (
    TestModel,
    TestPassageAssociation,
)
from app.infrastructure.persistence.models.user_model import UserModel


class SQLTestQueryService(TestQueryService):
    """SQL implementation using JOIN for efficient data retrieval"""

    async def get_test_by_id_with_details(
        self, test_id: str
    ) -> TestWithDetailsQueryModel:
        stmt = (
            select(
                TestModel,
                UserModel.id,
                UserModel.username,
                UserModel.email,
                UserModel.full_name,
            )
            .options(
                selectinload(TestModel.passage_associations)
                .selectinload(TestPassageAssociation.passage)
                .selectinload(PassageModel.question_groups)
                .selectinload(QuestionGroupModel.questions),
                selectinload(TestModel.passage_associations)
                .selectinload(TestPassageAssociation.passage)
                .selectinload(PassageModel.questions),
            )
            .join(UserModel, TestModel.created_by == UserModel.id, isouter=True)
            .where(TestModel.id == test_id)
            .where(TestModel.is_active == True)
        )

        resultset = await self.session.execute(stmt)
        try:
            result = resultset.one()
        except NoResultFound:
            raise TestNotFoundError(test_id)

        test_model = result[0]
        author_id = result[1]
        author_username = result[2]
        author_email = result[3]
        author_full_name = result[4]
        # Convert passage models to domain entities with questions
        passages = [p.to_domain() for p in test_model.passages]

        return TestWithDetailsQueryModel(
            id=test_model.id,
            title=test_model.title,
            description=test_model.description,
            test_type=TestType(test_model.test_type.value),
            time_limit_minutes=test_model.time_limit_minutes,
            total_questions=test_model.total_questions,
            total_points=test_model.total_points,
            status=TestStatus(test_model.status.value),
            created_by=AuthorInfo(
                id=author_id,
                username=author_username,
                email=author_email,
                full_name=author_full_name,
            ),
            created_at=test_model.created_at,
            updated_at=test_model.updated_at,
            is_active=test_model.is_active,
            passages=passages,
            passage_ids=[passage.id for passage in passages],
        )

    async def get_test_by_id_with_passages(
        self,
        test_id: str,
        status: Optional[TestStatus] = None,
        test_type: Optional[TestType] = None,
    ) -> TestWithPassagesQueryModel:
        stmt = (
            select(TestModel)
            .options(
                selectinload(TestModel.passage_associations).selectinload(
                    TestPassageAssociation.passage
                )
            )  # Eager load passages via association
            .where(TestModel.is_active == True)
            .where(TestModel.id == test_id)
        )

        if status:
            stmt = stmt.where(TestModel.status == status)
        if test_type:
            stmt = stmt.where(TestModel.test_type == test_type)

        results = await self.session.execute(stmt)
        try:
            test: TestModel = results.scalar_one()
        except NoResultFound:
            raise TestNotFoundError(test_id)

        # Convert PassageModel instances to Passage domain entities
        passage_entities = [self._convert_passage_to_entity(p) for p in test.passages]

        response = TestWithPassagesQueryModel(
            id=test.id,
            title=test.title,
            description=test.description,
            test_type=TestType(test.test_type.value),
            passage_ids=[passage.id for passage in test.passages],
            time_limit_minutes=test.time_limit_minutes,
            total_questions=test.total_questions,
            total_points=test.total_points,
            status=TestStatus(test.status.value),
            created_by=test.created_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            is_active=test.is_active,
            passages=passage_entities,
        )

        return response

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_with_authors(
        self,
        status: Optional[TestStatus] = None,
        test_type: Optional[TestType] = None,
    ) -> List[TestWithAuthorQueryModel]:
        """
        Fetch all tests with author information using optimized queries.

        Uses:
        - Query 1: Join tests with users to get test + author data
        - Query 2: Fetch all test-passage relationships
        - Aggregate passage IDs in Python (database-agnostic)
        """

        # Query 1: Get tests with author information
        stmt = (
            select(
                TestModel,
                UserModel.id.label("author_id"),
                UserModel.username.label("author_username"),
                UserModel.email.label("author_email"),
                UserModel.full_name.label("author_full_name"),
            )
            .join(UserModel, TestModel.created_by == UserModel.id)
            .where(TestModel.is_active == True)
        )

        # Apply filters if provided
        if status:
            stmt = stmt.where(TestModel.status == status.value)

        if test_type:
            stmt = stmt.where(TestModel.test_type == test_type.value)

        # Order by created_at descending (newest first)
        stmt = stmt.order_by(TestModel.created_at.desc())

        # Execute query
        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return []

        # Extract test IDs for passage lookup
        test_ids = [row[0].id for row in rows]

        # Query 2: Fetch all passage IDs for these tests (ordered by passage_order)
        passage_stmt = (
            select(TestPassageAssociation.test_id, TestPassageAssociation.passage_id)
            .where(TestPassageAssociation.test_id.in_(test_ids))
            .order_by(TestPassageAssociation.passage_order)
        )

        passage_result = await self.session.execute(passage_stmt)
        passage_rows = passage_result.all()

        # Build a map: test_id -> [passage_ids]
        test_passages_map = {}
        for test_id, passage_id in passage_rows:
            if test_id not in test_passages_map:
                test_passages_map[test_id] = []
            test_passages_map[test_id].append(passage_id)

        # Map results to query models
        query_models = []
        for row in rows:
            test_model = row[0]  # TestModel object
            author_id = row[1]
            author_username = row[2]
            author_email = row[3]
            author_full_name = row[4]

            # Get passage IDs from map (empty list if none)
            passage_ids = test_passages_map.get(test_model.id, [])

            query_model = TestWithAuthorQueryModel(
                id=test_model.id,
                title=test_model.title,
                description=test_model.description,
                test_type=TestType(
                    test_model.test_type.value
                ),  # Convert infrastructure enum to domain enum
                passage_ids=passage_ids,
                time_limit_minutes=test_model.time_limit_minutes,
                total_questions=test_model.total_questions,
                total_points=test_model.total_points,
                status=TestStatus(
                    test_model.status.value
                ),  # Convert infrastructure enum to domain enum
                created_at=test_model.created_at,
                updated_at=test_model.updated_at,
                is_active=test_model.is_active,
                author=AuthorInfo(
                    id=author_id,
                    username=author_username,
                    email=author_email,
                    full_name=author_full_name,
                ),
            )
            query_models.append(query_model)

        return query_models

    @staticmethod
    def _convert_passage_to_entity(passage_model: PassageModel) -> Passage:
        """Convert PassageModel to Passage domain entity (without questions)"""
        return Passage(
            id=passage_model.id,
            title=passage_model.title,
            content=passage_model.content,
            word_count=passage_model.word_count or 0,
            difficulty_level=passage_model.difficulty_level or 1,
            topic=passage_model.topic or "General",
            source=passage_model.source,
            created_by=passage_model.created_by,
            created_at=passage_model.created_at,
            updated_at=passage_model.updated_at,
            is_active=passage_model.is_active,
        )
