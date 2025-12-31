"""Passage Aggregate Root"""
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.passage.constants import (
    MAX_DIFFICULTY_LEVEL,
    MAX_TITLE_LENGTH,
    MAX_TOPIC_LENGTH,
    MIN_CONTENT_LENGTH,
    MIN_DIFFICULTY_LEVEL,
    MIN_WORD_COUNT,
)
from app.domain.aggregates.passage.question import Question
from app.domain.aggregates.passage.question_group import QuestionGroup
from app.domain.errors.passage_errors import InvalidPassageDataError
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
    - A passage must have at least one question before validation
    - Question numbers must be sequential within the passage
    - Questions in a group must match the group's question type
    - Total questions must match the count of actual questions
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    content: str = Field(min_length=MIN_CONTENT_LENGTH)
    word_count: int = Field(ge=MIN_WORD_COUNT)
    difficulty_level: int = Field(ge=MIN_DIFFICULTY_LEVEL, le=MAX_DIFFICULTY_LEVEL)
    topic: str = Field(min_length=1, max_length=MAX_TOPIC_LENGTH)
    source: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    # Owned entities (part of aggregate)
    question_groups: List[QuestionGroup] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)

    def add_question_group(self, group: QuestionGroup) -> None:
        """
        Add a question group to the passage

        Raises:
            DuplicateQuestionGroupOrderError: If a group with the same order exists
        """
        if any(qg.order_in_passage == group.order_in_passage for qg in self.question_groups):
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

        Raises:
            QuestionGroupNotFoundError: If question references non-existent group
            QuestionTypeMismatchError: If question type doesn't match group type
            QuestionNumberOutOfRangeError: If question number not in group range
        """
        if question.question_group_id:
            group = self.get_question_group_by_id(question.question_group_id)
            if not group:
                raise QuestionGroupNotFoundError(question.question_group_id)

            if question.question_type != group.question_type:
                raise QuestionTypeMismatchError(
                    question.question_type.value,
                    group.question_type.value
                )

            if not group.contains_question_number(question.question_number):
                raise QuestionNumberOutOfRangeError(
                    question.question_number,
                    group.start_question_number,
                    group.end_question_number
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

        Raises:
            InvalidPassageDataError: If passage has no questions or invalid references
        """
        if not self.questions:
            raise InvalidPassageDataError("Passage must have at least one question")

        # Validate all questions in groups reference valid groups
        for question in self.questions:
            if question.question_group_id:
                if not self.get_question_group_by_id(question.question_group_id):
                    raise InvalidPassageDataError(
                        f"Question {question.id} references non-existent group {question.question_group_id}"
                    )
