from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.passage import Passage
from app.domain.entities.question import Question, QuestionGroup, QuestionType
from app.domain.entities.test import Test, TestStatus, TestType
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.infrastructure.persistence.models.passage_model import PassageModel
from app.infrastructure.persistence.models.question_model import (
    QuestionGroupModel,
    QuestionModel,
)
from app.infrastructure.persistence.models.test_model import (
    TestModel,
    test_passages,
)


class SQLTestRepository(TestRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, test: Test) -> Test:
        """Create a new test"""
        test_model = TestModel(
            id=test.id,
            title=test.title,
            description=test.description,
            test_type=test.test_type.value,
            time_limit_minutes=test.time_limit_minutes,
            total_questions=test.total_questions,
            total_points=test.total_points,
            status=test.status.value,
            created_by=test.created_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            is_active=test.is_active,
        )

        self.session.add(test_model)
        await self.session.commit()
        await self.session.refresh(test_model)

        return self._to_domain_entity(test_model)

    async def get_by_id(self, test_id: str) -> Optional[Test]:
        """Get a test by ID with its passages"""
        stmt = (
            select(TestModel)
            .options(selectinload(TestModel.passages))
            .filter_by(id=test_id)
        )
        result = await self.session.execute(stmt)
        test_model = result.scalar_one_or_none()

        if test_model:
            return self._to_domain_entity(test_model)
        return None

    async def get_all(self) -> List[Test]:
        """Get all tests"""
        stmt = select(TestModel).options(selectinload(TestModel.passages))
        result = await self.session.execute(stmt)
        test_models = result.scalars().all()

        return [self._to_domain_entity(tm) for tm in test_models]

    async def update(self, test: Test) -> Test:
        """Update an existing test"""
        stmt = select(TestModel).filter_by(id=test.id)
        result = await self.session.execute(stmt)
        test_model = result.scalar_one_or_none()

        if not test_model:
            raise ValueError(f"Test with id {test.id} not found")

        # Update basic fields
        test_model.title = test.title
        test_model.description = test.description
        test_model.test_type = test.test_type.value
        test_model.time_limit_minutes = test.time_limit_minutes
        test_model.total_questions = test.total_questions
        test_model.total_points = test.total_points
        test_model.status = test.status.value
        test_model.updated_at = test.updated_at
        test_model.is_active = test.is_active

        await self.session.commit()
        await self.session.refresh(test_model)

        return self._to_domain_entity(test_model)

    async def delete(self, test_id: str) -> bool:
        """Soft delete a test"""
        stmt = select(TestModel).filter_by(id=test_id)
        result = await self.session.execute(stmt)
        test_model = result.scalar_one_or_none()

        if not test_model:
            return False

        test_model.is_active = False
        await self.session.commit()
        return True

    async def add_passage_to_test(
        self, test_id: str, passage_id: str, passage_order: int
    ) -> None:
        """Add a passage to a test with specific order"""
        from sqlalchemy import insert

        stmt = insert(test_passages).values(
            test_id=test_id, passage_id=passage_id, passage_order=passage_order
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def get_test_with_full_passages(self, test_id: str) -> Optional[Test]:
        """Get a test with full passage data including questions and question groups"""
        stmt = (
            select(TestModel)
            .options(
                selectinload(TestModel.passages).selectinload(PassageModel.questions),
                selectinload(TestModel.passages).selectinload(
                    PassageModel.question_groups
                ),
            )
            .filter_by(id=test_id)
        )
        result = await self.session.execute(stmt)
        test_model = result.scalar_one_or_none()

        if not test_model:
            return None

        # Convert to domain entity with full passage data
        test = self._to_domain_entity(test_model)
        return test

    def _to_domain_entity(self, test_model: TestModel) -> Test:
        """Convert TestModel to Test domain entity"""
        passage_ids = [p.id for p in test_model.passages] if test_model.passages else []

        return Test(
            id=test_model.id,
            title=test_model.title,
            description=test_model.description,
            test_type=TestType(test_model.test_type),
            passage_ids=passage_ids,
            time_limit_minutes=test_model.time_limit_minutes,
            total_questions=test_model.total_questions,
            total_points=test_model.total_points,
            status=TestStatus(test_model.status),
            created_by=test_model.created_by,
            created_at=test_model.created_at,
            updated_at=test_model.updated_at,
            is_active=test_model.is_active,
        )
