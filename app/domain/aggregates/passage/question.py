"""Question Entity - Part of Passage Aggregate"""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.aggregates.passage.constants import (
    DEFAULT_QUESTION_POINTS,
    MIN_QUESTION_POINTS,
)
from app.domain.aggregates.passage.question_type import QuestionType
from app.domain.errors.question_errors import MissingOptionsError
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option


class Question(BaseModel):
    """
    Entity: A single question in a passage
    Part of Passage Aggregate - should not be accessed independently
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_group_id: Optional[str] = None
    question_number: int = Field(ge=1)
    question_type: QuestionType
    question_text: str = Field(min_length=1)
    options: Optional[List[Option]] = None
    correct_answer: CorrectAnswer
    explanation: Optional[str] = None
    instructions: Optional[str] = None  # Individual instruction (if not in group)
    points: int = Field(default=DEFAULT_QUESTION_POINTS, ge=MIN_QUESTION_POINTS)
    order_in_passage: int = Field(ge=1)

    @field_validator("options")
    @classmethod
    def validate_options_for_type(cls, v, info):
        """Validate that options exist for question types that need them"""
        if "question_type" not in info.data:
            return v

        question_type = info.data["question_type"]

        if QuestionType.does_question_require_options(question_type) and not v:
            raise MissingOptionsError(question_type.value)

        return v

    def check_answer(self, student_answer) -> bool:
        """Check if student answer is correct"""
        return self.correct_answer.is_correct(student_answer)
