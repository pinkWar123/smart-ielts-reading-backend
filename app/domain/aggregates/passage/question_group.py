"""Question Group Entity - Part of Passage Aggregate"""

import uuid

from pydantic import BaseModel, Field, field_validator

from app.domain.aggregates.passage.question_type import QuestionType
from app.domain.errors.question_errors import InvalidQuestionGroupRangeError


class QuestionGroup(BaseModel):
    """
    Entity: A group of questions with shared instructions (common in IELTS)
    Part of Passage Aggregate - should not be accessed independently
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    group_instructions: str = Field(..., min_length=1)
    question_type: QuestionType
    start_question_number: int = Field(ge=1)
    end_question_number: int = Field(ge=1)
    order_in_passage: int = Field(ge=1)

    @field_validator("end_question_number")
    @classmethod
    def validate_question_range(cls, v, info):
        """Ensure end_question_number >= start_question_number"""
        if (
            "start_question_number" in info.data
            and v < info.data["start_question_number"]
        ):
            start = info.data["start_question_number"]
            raise InvalidQuestionGroupRangeError(start, v)
        return v

    def contains_question_number(self, question_number: int) -> bool:
        """Check if this group contains the given question number"""
        return self.start_question_number <= question_number <= self.end_question_number
