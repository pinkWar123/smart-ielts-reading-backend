from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.attempt.attempt import Answer, AttemptStatus, TabViolation
from app.domain.aggregates.attempt.text_highlight import TextHighlight
from app.domain.aggregates.class_ import Class
from app.domain.aggregates.session import Session
from app.domain.aggregates.test import Test


class AttemptDetail(BaseModel):
    id: str
    student_id: str
    started_at: datetime
    status: AttemptStatus
    submitted_at: datetime | None
    time_remaining_seconds: int | None
    answers: List[Answer]
    tab_violations: List[TabViolation]
    highlighted_text: List[TextHighlight]
    current_passage_index: int
    current_question_index: int
    test: Optional[Test]
    session: Optional[Session]
    class_: Optional[Class]
