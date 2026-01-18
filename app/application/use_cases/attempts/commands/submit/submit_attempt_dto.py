from datetime import datetime
from typing import List

from pydantic import BaseModel

from app.domain.aggregates.attempt.attempt import Answer, AttemptStatus, SubmitType


class SubmitAttemptRequest(BaseModel):
    attempt_id: str
    submit_type: SubmitType

    class Config:
        use_enum_values = True


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: AttemptStatus
    submitted_at: datetime
    score: float
    total_questions: int
    answers: List[Answer]
    answered_questions: int
    time_taken_seconds: int

    class Config:
        use_enum_values = True
