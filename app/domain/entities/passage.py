"""Passage Aggregate Root"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.common.utils.time_helper import TimeHelper
from app.domain.entities.question import Question, QuestionGroup
from app.domain.errors.passage_errors import (
    InvalidQuestionReferenceError,
    NoQuestionsError,
)
from app.domain.errors.question_errors import (
    DuplicateQuestionGroupOrderError,
    QuestionGroupNotFoundError,
    QuestionNumberOutOfRangeError,
    QuestionTypeMismatchError,
)


class Passage(BaseModel):
    """
    Aggregate Root: Passage with Questions and QuestionGroups

    Business Rules:
    - A passage must have at least one question
    - Question numbers must be sequential within the passage
    - Questions in a group must match the group's question type
    - Total questions must match the count of actual questions
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    word_count: int = Field(ge=0)
    difficulty_level: int = Field(ge=1, le=5)
    topic: str = Field(min_length=1, max_length=255)
    source: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Owned entities (part of aggregate)
    question_groups: List[QuestionGroup] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)

    @field_validator("questions")
    @classmethod
    def validate_questions_not_empty(cls, v):
        """Ensure passage has at least one question when being validated"""
        # Allow empty during construction, but enforce in domain methods
        return v

    def add_question_group(self, group: QuestionGroup) -> None:
        """Add a question group to the passage"""
        # Validate order uniqueness
        if any(
            qg.order_in_passage == group.order_in_passage for qg in self.question_groups
        ):
            raise DuplicateQuestionGroupOrderError(group.order_in_passage)

        self.question_groups.append(group)
        self.updated_at = TimeHelper.utc_now()

    def add_question(self, question: Question) -> None:
        """
        Add a question to the passage

        Business rules enforced:
        - Question must belong to a valid group if group_id is set
        - Question type must match group type if in a group
        - Question number must match group range if in a group
        """
        if question.question_group_id:
            group = self.get_question_group_by_id(question.question_group_id)
            if not group:
                raise QuestionGroupNotFoundError(question.question_group_id)

            if question.question_type != group.question_type:
                raise QuestionTypeMismatchError(
                    question.question_type.value, group.question_type.value
                )

            if not group.contains_question_number(question.question_number):
                raise QuestionNumberOutOfRangeError(
                    question.question_number,
                    group.start_question_number,
                    group.end_question_number,
                )

        self.questions.append(question)
        self.updated_at = TimeHelper.utc_now()

    def get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Get a question by its ID"""
        return next((q for q in self.questions if q.id == question_id), None)

    def get_question_group_by_id(self, group_id: str) -> Optional[QuestionGroup]:
        """Get a question group by its ID"""
        return next((qg for qg in self.question_groups if qg.id == group_id), None)

    def get_questions_by_group(self, group_id: str) -> List[Question]:
        """Get all questions belonging to a specific group"""
        return [q for q in self.questions if q.question_group_id == group_id]

    def get_total_questions(self) -> int:
        """Get total number of questions in the passage"""
        return len(self.questions)

    def get_total_points(self) -> int:
        """Calculate total points for all questions in the passage"""
        return sum(q.points for q in self.questions)

    def remove_question(self, question_id: str) -> None:
        """Remove a question from the passage"""
        self.questions = [q for q in self.questions if q.id != question_id]
        self.updated_at = TimeHelper.utc_now()

    def remove_question_group(self, group_id: str) -> None:
        """
        Remove a question group and all its questions from the passage
        """
        # Remove all questions in the group
        self.questions = [q for q in self.questions if q.question_group_id != group_id]

        # Remove the group itself
        self.question_groups = [qg for qg in self.question_groups if qg.id != group_id]
        self.updated_at = TimeHelper.utc_now()

    def validate_integrity(self) -> None:
        """
        Validate aggregate integrity
        Should be called before persisting
        """
        if not self.questions:
            raise NoQuestionsError()

        # Validate all questions in groups reference valid groups
        for question in self.questions:
            if question.question_group_id:
                if not self.get_question_group_by_id(question.question_group_id):
                    raise InvalidQuestionReferenceError(
                        question.id, question.question_group_id
                    )
