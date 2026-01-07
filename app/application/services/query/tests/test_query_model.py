"""Test Query Models

Read-optimized data models for test queries.
These are NOT domain entities - they are flattened DTOs designed for efficient reads.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType
from app.domain.entities.passage import Passage


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
