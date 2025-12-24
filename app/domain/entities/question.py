import uuid
from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOTGIVEN = "TRUE_FALSE_NOTGIVEN"
    YES_NO_NOTGIVEN = "YES_NO_NOTGIVEN"
    MATCHING_HEADINGS = "MATCHING_HEADINGS"
    MATCHING_INFORMATION = "MATCHING_INFORMATION"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"
    SHORT_ANSWER = "SHORT_ANSWER"


class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    passage_id: str
    question_number: int = Field(ge=1)
    question_type: QuestionType
    question_text: str = Field(min_length=1)
    options: Optional[List[str]] = None
    correct_answer: Union[str, List[str]]
    explanation: Optional[str] = None
    points: int = Field(default=1, ge=1)
    order_in_passage: int = Field(ge=1)
