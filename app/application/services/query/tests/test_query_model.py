"""Test Query Models

Read-optimized data models for test queries.
These are NOT domain entities - they are flattened DTOs designed for efficient reads.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.common.pagination import PaginatedResponse
from app.domain.aggregates.passage import Passage
from app.domain.aggregates.passage.question import QuestionType
from app.domain.aggregates.test import Test
from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType


class AuthorInfo(BaseModel):
    """Author information embedded in test queries"""

    id: str
    username: str
    email: str
    full_name: str


class TestWithAuthorQueryModel(BaseModel):
    """
    Read model for test with author information.

    This model is optimized for queries and contains denormalized data
    from multiple aggregates (Test and User).
    """

    # Test fields
    id: str
    title: str
    description: Optional[str]
    test_type: TestType
    passage_ids: list[str]
    time_limit_minutes: int
    total_questions: int
    total_points: int
    status: TestStatus
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    # Author information (denormalized from User aggregate)
    author: AuthorInfo


class TestWithPassagesQueryModel(BaseModel):
    id: str
    title: str
    description: Optional[str]
    test_type: TestType
    passage_ids: list[str]
    time_limit_minutes: int
    total_questions: int
    total_points: int
    status: TestStatus
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    passages: list[Passage]

    def to_domain_entity(self) -> Test:
        """Convert query model to domain entity"""
        return Test(
            id=self.id,
            title=self.title,
            description=self.description,
            test_type=self.test_type,
            passage_ids=self.passage_ids,
            time_limit_minutes=self.time_limit_minutes,
            total_questions=self.total_questions,
            total_points=self.total_points,
            status=self.status,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
        )


class TestWithDetailsQueryModel(TestWithPassagesQueryModel):
    """Test query model with detailed passage and question info"""

    # Additional detailed fields can be added here as needed
    created_by: AuthorInfo

    def to_domain_entity(self) -> Test:
        """Convert query model to domain entity"""
        return Test(
            id=self.id,
            title=self.title,
            description=self.description,
            test_type=self.test_type,
            passage_ids=self.passage_ids,
            time_limit_minutes=self.time_limit_minutes,
            total_questions=self.total_questions,
            total_points=self.total_points,
            status=self.status,
            created_by=self.created_by.id,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
        )


class TestWithQuestionTypesQueryModel(BaseModel):
    id: str
    title: str
    question_types: List[QuestionType]


class PaginatedTestsWithQuestionTypesQueryModel(
    PaginatedResponse[TestWithQuestionTypesQueryModel]
):
    pass
