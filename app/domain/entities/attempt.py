import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AttemptStatus:
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ABANDONED = "ABANDONED"


class TabViolation(BaseModel):
    timestamp: datetime
    violation_type: str


class Answer(BaseModel):
    question_id: str
    student_answer: str
    is_correct: bool
    points_earned: int = 0
    answered_at: datetime


class Attempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    student_id: str
    status: AttemptStatus = AttemptStatus.IN_PROGRESS
    started_at: datetime = Field(default_factory=lambda: datetime.now)
    submitted_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    answers: List[Answer] = Field(default_factory=list)
    tab_violations: List[TabViolation] = Field(default_factory=list)
    total_score: Optional[int] = None
    percentage_score: Optional[float] = None
    current_passage_index: int = Field(default=0, ge=0)
    current_question_index: int = Field(default=0, ge=0)
