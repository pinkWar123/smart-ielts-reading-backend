"""Question domain entities - Part of Passage Aggregate"""

import uuid
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.errors.question_errors import (
    InvalidQuestionGroupRangeError,
    InvalidQuestionOptionsError,
    MissingOptionsError,
)
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option


class QuestionType(str, Enum):
    """IELTS Reading question types"""

    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOTGIVEN = "TRUE_FALSE_NOTGIVEN"
    YES_NO_NOTGIVEN = "YES_NO_NOTGIVEN"
    MATCHING_HEADINGS = "MATCHING_HEADINGS"
    MATCHING_INFORMATION = "MATCHING_INFORMATION"
    MATCHING_FEATURES = "MATCHING_FEATURES"
    MATCHING_SENTENCE_ENDINGS = "MATCHING_SENTENCE_ENDINGS"
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"
    NOTE_COMPLETION = "NOTE_COMPLETION"
    TABLE_COMPLETION = "TABLE_COMPLETION"
    FLOW_CHART_COMPLETION = "FLOW_CHART_COMPLETION"
    DIAGRAM_LABEL_COMPLETION = "DIAGRAM_LABEL_COMPLETION"
    SHORT_ANSWER = "SHORT_ANSWER"


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
    options: Optional[List[Option]] = Field(
        None, description="Shared options for all questions in this group"
    )

    @field_validator("end_question_number")
    @classmethod
    def validate_question_range(cls, v, info):
        """Ensure end_question_number >= start_question_number"""
        if (
            "start_question_number" in info.data
            and v < info.data["start_question_number"]
        ):
            raise InvalidQuestionGroupRangeError(info.data["start_question_number"], v)
        return v

    @field_validator("options")
    @classmethod
    def validate_group_options(cls, v, info):
        """Validate that options exist for question types that need them at group level"""
        if "question_type" not in info.data:
            return v

        question_type = info.data["question_type"]
        # Question types that use group-level options
        needs_group_options = question_type in [
            QuestionType.MATCHING_HEADINGS,
            QuestionType.MATCHING_INFORMATION,
            QuestionType.MATCHING_FEATURES,
            QuestionType.MATCHING_SENTENCE_ENDINGS,
        ]

        if needs_group_options and not v:
            raise MissingOptionsError(question_type.value)

        return v

    def contains_question_number(self, question_number: int) -> bool:
        """Check if this group contains the given question number"""
        return self.start_question_number <= question_number <= self.end_question_number


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
    points: int = Field(default=1, ge=1)
    order_in_passage: int = Field(ge=1)

    @field_validator("options")
    @classmethod
    def validate_options_for_type(cls, v, info):
        """Validate that options exist for question types that need them"""
        if "question_type" not in info.data:
            return v

        question_type = info.data["question_type"]
        question_group_id = info.data.get("question_group_id")

        # Question types that use group-level options (not stored on individual questions)
        uses_group_options = question_type in [
            QuestionType.MATCHING_HEADINGS,
            QuestionType.MATCHING_INFORMATION,
            QuestionType.MATCHING_FEATURES,
            QuestionType.MATCHING_SENTENCE_ENDINGS,
        ]

        # Question types that need their own options (stored on each question)
        needs_own_options = question_type in [
            QuestionType.MULTIPLE_CHOICE,
        ]

        # If question belongs to a group and uses group-level options, it should NOT have its own options
        if question_group_id and uses_group_options:
            if v:
                raise InvalidQuestionOptionsError(question_type.value)
            return v

        # If question needs its own options (like MULTIPLE_CHOICE), validate they exist
        if needs_own_options and not v:
            raise MissingOptionsError(question_type.value)

        return v

    def check_answer(self, student_answer) -> bool:
        """Check if student answer is correct"""
        return self.correct_answer.is_correct(student_answer)
