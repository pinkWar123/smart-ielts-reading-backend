import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class TestType(str, Enum):
    FULL_TEST = "FULL_TEST"
    SINGLE_PASSAGE = "SINGLE_PASSAGE"


class TestStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Test(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: TestType
    passage_ids: List[str] = []
    time_limit_minutes: int = Field(ge=1)
    total_questions: int = Field(ge=1)
    total_points: int = Field(ge=1)
    status: TestStatus = Field(default=TestStatus.DRAFT)
    created_by: str
    updated_at: Optional[datetime] = None
    is_active: bool = True
