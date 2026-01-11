import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.attempt.text_highlight import TextHighlight
from app.domain.errors.attempt_errors import (
    AttemptAlreadySubmittedError,
    InvalidAttemptStatusError,
)
from app.domain.errors.highlight_errors import HighlightNotFoundError


class AttemptStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    ABANDONED = "ABANDONED"


class TabViolation(BaseModel):
    timestamp: datetime
    violation_type: str


class Answer(BaseModel):
    question_id: str
    student_answer: str
    is_correct: bool
    points_earned: int = 0
    answered_at: datetime


class Attempt(BaseModel):
    """
    Aggregate Root: Attempt

    Represents a student's attempt at taking a test.

    Business Rules:
    - Can only modify if status is IN_PROGRESS
    - Once submitted, cannot be modified
    - Tracks all student activities for monitoring
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    test_id: str
    student_id: str
    session_id: Optional[str] = (
        None  # Reference to Session aggregate (if part of a session)
    )
    status: AttemptStatus = Field(default=AttemptStatus.IN_PROGRESS)
    started_at: datetime = Field(default_factory=TimeHelper.utc_now)
    submitted_at: Optional[datetime] = None
    time_remaining_seconds: Optional[int] = None
    answers: List[Answer] = Field(default_factory=list)
    tab_violations: List[TabViolation] = Field(default_factory=list)
    highlighted_text: List[TextHighlight] = Field(default_factory=list)
    total_correct_answers: Optional[int] = None
    band_score: Optional[float] = None
    current_passage_index: int = Field(default=0, ge=0)
    current_question_index: int = Field(default=0, ge=0)

    def record_tab_violation(self, violation_type: str = "TAB_SWITCH") -> None:
        """
        Record a tab switching violation

        Args:
            violation_type: Type of violation (default: "TAB_SWITCH")
        """
        self.tab_violations.append(
            TabViolation(timestamp=TimeHelper.utc_now(), violation_type=violation_type)
        )

    def record_text_highlight(
        self, text: str, passage_id: str, start: int, end: int
    ) -> None:
        """
        Record a text highlighting action

        Args:
            text: The highlighted text
            passage_id: ID of the passage containing the text
            start: Start position in the passage
            end: End position in the passage
        """
        self.highlighted_text.append(
            TextHighlight(
                timestamp=TimeHelper.utc_now(),
                text=text,
                passage_id=passage_id,
                position_start=start,
                position_end=end,
                comment=None,
            )
        )

    def add_comment_to_highlight(
        self, comment: str, passage_id: str, highlight_id: str
    ):
        highlight = next(
            filter(lambda h: h.id == highlight_id, self.highlighted_text), None
        )
        if not highlight:
            raise HighlightNotFoundError(highlight_id)
        highlight.set_comment(comment)

    def remove_highlight(self, highlight_id: str):
        self.highlighted_text = self.highlighted_text.remove()

    def update_progress(self, passage_index: int, question_index: int) -> None:
        """
        Update current position in test

        Args:
            passage_index: Current passage index (0-based)
            question_index: Current question index (0-based)
        """
        self.current_passage_index = passage_index
        self.current_question_index = question_index

    def submit_answer(self, answer: Answer) -> None:
        """
        Submit or update an answer

        Business rules:
        - If answer for same question exists, replace it
        - Otherwise, add new answer

        Args:
            answer: The answer to submit
        """
        # Remove existing answer for same question if exists
        self.answers = [a for a in self.answers if a.question_id != answer.question_id]
        self.answers.append(answer)

    def update_time_remaining(self, seconds: int) -> None:
        """
        Update remaining time

        Args:
            seconds: Remaining time in seconds
        """
        self.time_remaining_seconds = seconds

    def submit_attempt(self) -> None:
        """
        Mark attempt as submitted

        Business rules:
        - Can only submit if status is IN_PROGRESS

        Raises:
            InvalidAttemptStatusError: If attempt is not IN_PROGRESS
            AttemptAlreadySubmittedError: If attempt was already submitted
        """
        if self.status == AttemptStatus.SUBMITTED:
            raise AttemptAlreadySubmittedError(self.id)

        if self.status != AttemptStatus.IN_PROGRESS:
            raise InvalidAttemptStatusError(self.id, self.status)

        self.status = AttemptStatus.SUBMITTED
        self.submitted_at = TimeHelper.utc_now()

    def abandon_attempt(self) -> None:
        """
        Mark attempt as abandoned

        Used when a student disconnects for too long or violates rules.
        """
        self.status = AttemptStatus.ABANDONED
        self.submitted_at = TimeHelper.utc_now()

    def get_answer_count(self) -> int:
        """
        Get the number of answers submitted

        Returns:
            Number of submitted answers
        """
        return len(self.answers)

    def get_violation_count(self) -> int:
        """
        Get the number of tab violations

        Returns:
            Number of tab violations
        """
        return len(self.tab_violations)

    def get_highlight_count(self) -> int:
        """
        Get the number of text highlights

        Returns:
            Number of text highlights
        """
        return len(self.highlighted_text)
