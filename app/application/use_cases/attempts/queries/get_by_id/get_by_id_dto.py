from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.attempt.attempt import Answer, AttemptStatus, TabViolation
from app.domain.aggregates.attempt.text_highlight import TextHighlight
from app.domain.aggregates.test import Test, TestType


class GetAttemptByIdQuery(BaseModel):
    id: str


class TestInfo(BaseModel):
    id: str
    title: str
    test_type: TestType
    time_limit_minutes: int
    passage_count: int


class CurrentProgress(BaseModel):
    passage_index: int
    question_index: int
    total_questions: int
    answer_count: int


class AnswerDTO(BaseModel):
    question_id: str
    student_answer: str


class GetAttemptByIdResponse(BaseModel):
    id: str
    session_id: Optional[str] = None
    test_id: Optional[str] = None
    student_id: Optional[str] = None
    status: AttemptStatus
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    test_info: Optional[TestInfo]
    current_progress: Optional[CurrentProgress]
    answers: List[AnswerDTO]
    highlights: List[TextHighlight]
    violations: List[TabViolation]
