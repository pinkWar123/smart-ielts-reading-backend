from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.test import TestStatus, TestType


class PublishTestRequest(BaseModel):
    id: str


class PassageDTO(BaseModel):
    id: str
    title: str
    reduced_content: str
    word_count: int
    difficulty_level: int
    topic: str
    source: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class PublishTestResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    test_type: TestType
    passage_ids: List[str]
    time_limit_minutes: int
    total_questions: int
    total_points: int
    status: TestStatus
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True
    passages: List[PassageDTO]
