from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UpdateAnswerRequest(BaseModel):
    attempt_id: str
    question_id: str
    answer: str


class UpdateAnswerResponse(BaseModel):
    question_id: str
    question_number: Optional[int]
    answer: str
    submitted_at: Optional[datetime]
    is_updated: bool
