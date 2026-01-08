"""DTOs for Get All Tests Use Case"""

from typing import Optional

from pydantic import BaseModel

from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType


class Author(BaseModel):
    """Author information in test response"""

    id: str
    username: str
    email: str
    full_name: str


class TestResponse(BaseModel):
    """Individual test in the response"""

    test_id: str
    title: str
    passage_count: int
    status: TestStatus
    type: TestType
    time_limit_minutes: int
    total_points: int
    total_questions: int
    created_by: Author


class GetAllTestsResponse(BaseModel):
    """Response containing list of tests"""

    tests: list[TestResponse]


class GetAllTestsQueryParams(BaseModel):
    """Query parameters for filtering tests"""

    status: Optional[TestStatus] = None
    type: Optional[TestType] = None
