from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.entities.test import Test, TestStatus, TestType


class CreateTestRequest(BaseModel):
    """Request to create a new empty test"""

    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: TestType
    time_limit_minutes: int = Field(ge=1, description="Time limit in minutes")


class AddPassageToTestRequest(BaseModel):
    """Request to add a complete passage to a test"""

    passage_id: str = Field(description="ID of the passage to add")


class TestResponse(BaseModel):
    """Response containing test data"""

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

    @classmethod
    def from_entity(cls, test: Test) -> "TestResponse":
        """Create a TestResponse from a Test domain entity"""
        return cls(
            id=test.id,
            title=test.title,
            description=test.description,
            test_type=test.test_type,
            passage_ids=test.passage_ids,
            time_limit_minutes=test.time_limit_minutes,
            total_questions=test.total_questions,
            total_points=test.total_points,
            status=test.status,
            created_by=test.created_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            is_active=test.is_active,
        )
