"""SQL implementation of Test Query Service

This implementation uses optimized SQL queries with JOINs to fetch test data
with author information in a single database round-trip.
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.query.tests.test_query_model import (
    AuthorInfo,
    TestWithAuthorQueryModel,
)
from app.application.services.query.tests.test_query_service import TestQueryService
from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType
from app.infrastructure.persistence.models.test_model import (
    TestModel,
    test_passages,
)
from app.infrastructure.persistence.models.user_model import UserModel


class SQLTestQueryService(TestQueryService):
    """SQL implementation using JOIN for efficient data retrieval"""

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

        # Query 2: Fetch all passage IDs for these tests
        passage_stmt = select(
            test_passages.c.test_id, test_passages.c.passage_id
        ).where(test_passages.c.test_id.in_(test_ids))

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
