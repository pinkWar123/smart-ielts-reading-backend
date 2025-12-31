"""Test Aggregate Root"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.test.constants import (
    FULL_TEST_PASSAGE_COUNT,
    MAX_TITLE_LENGTH,
    MIN_TIME_LIMIT_MINUTES,
    MIN_TOTAL_POINTS,
    MIN_TOTAL_QUESTIONS,
    SINGLE_PASSAGE_COUNT,
)
from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType
from app.domain.errors.test_errors import (
    DuplicatePassageError,
    InvalidTestStatusError,
    MaxPassageCountExceededError,
    NoPassagesError,
    PassageCountMismatchError,
    TestAlreadyArchivedError,
    TestPublishedError,
)


class Test(BaseModel):
    """
    Aggregate Root: Test

    Business Rules:
    - FULL_TEST must have exactly 3 passages
    - SINGLE_PASSAGE must have exactly 1 passage
    - Cannot publish without passages
    - Cannot modify passages once published
    - Total questions and points should match sum of all passages
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=MAX_TITLE_LENGTH)
    description: Optional[str] = None
    test_type: TestType
    passage_ids: List[str] = Field(
        default_factory=list
    )  # References to Passage aggregates
    time_limit_minutes: int = Field(ge=MIN_TIME_LIMIT_MINUTES)
    total_questions: int = Field(ge=MIN_TOTAL_QUESTIONS)
    total_points: int = Field(ge=MIN_TOTAL_POINTS)
    status: TestStatus = Field(default=TestStatus.DRAFT)
    created_by: str
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    updated_at: Optional[datetime] = None
    is_active: bool = True

    @field_validator("passage_ids")
    @classmethod
    def validate_passage_count(cls, v, info):
        """Validate passage count based on test type"""
        if "test_type" not in info.data:
            return v

        test_type = info.data["test_type"]

        if test_type == TestType.FULL_TEST and len(v) > FULL_TEST_PASSAGE_COUNT:
            raise MaxPassageCountExceededError(test_type.value, FULL_TEST_PASSAGE_COUNT)
        elif test_type == TestType.SINGLE_PASSAGE and len(v) > SINGLE_PASSAGE_COUNT:
            raise MaxPassageCountExceededError(test_type.value, SINGLE_PASSAGE_COUNT)

        return v

    def add_passage(self, passage_id: str) -> None:
        """
        Add a passage to the test

        Business rules:
        - Cannot add passages to published tests
        - Must respect passage count limits for test type

        Raises:
            TestPublishedError: If test is already published
            MaxPassageCountExceededError: If passage count limit exceeded
            DuplicatePassageError: If passage already exists in test
        """
        if self.status == TestStatus.PUBLISHED:
            raise TestPublishedError("add passages")

        max_count = (
            FULL_TEST_PASSAGE_COUNT
            if self.test_type == TestType.FULL_TEST
            else SINGLE_PASSAGE_COUNT
        )

        if len(self.passage_ids) >= max_count:
            raise MaxPassageCountExceededError(self.test_type.value, max_count)

        if passage_id in self.passage_ids:
            raise DuplicatePassageError(passage_id)

        self.passage_ids.append(passage_id)
        self.updated_at = TimeHelper.utc_now()

    def remove_passage(self, passage_id: str) -> None:
        """
        Remove a passage from the test

        Raises:
            TestPublishedError: If test is already published
        """
        if self.status == TestStatus.PUBLISHED:
            raise TestPublishedError("remove passages")

        self.passage_ids = [pid for pid in self.passage_ids if pid != passage_id]
        self.updated_at = TimeHelper.utc_now()

    def publish(self) -> None:
        """
        Publish the test

        Business rules:
        - Must have correct number of passages
        - Must be in DRAFT status

        Raises:
            InvalidTestStatusError: If test is not in DRAFT status
            PassageCountMismatchError: If passage count doesn't match requirement
        """
        if self.status != TestStatus.DRAFT:
            raise InvalidTestStatusError(self.status.value, TestStatus.DRAFT.value)

        required_passages = (
            FULL_TEST_PASSAGE_COUNT
            if self.test_type == TestType.FULL_TEST
            else SINGLE_PASSAGE_COUNT
        )

        if len(self.passage_ids) != required_passages:
            raise PassageCountMismatchError(
                self.test_type.value, required_passages, len(self.passage_ids)
            )

        self.status = TestStatus.PUBLISHED
        self.updated_at = TimeHelper.utc_now()

    def archive(self) -> None:
        """
        Archive the test

        Raises:
            TestAlreadyArchivedError: If test is already archived
        """
        if self.status == TestStatus.ARCHIVED:
            raise TestAlreadyArchivedError()

        self.status = TestStatus.ARCHIVED
        self.updated_at = TimeHelper.utc_now()

    def update_totals(self, total_questions: int, total_points: int) -> None:
        """
        Update total questions and points
        Should be called after passages are modified

        Raises:
            TestPublishedError: If test is already published
        """
        if self.status == TestStatus.PUBLISHED:
            raise TestPublishedError("update totals")

        self.total_questions = total_questions
        self.total_points = total_points
        self.updated_at = TimeHelper.utc_now()

    def validate_integrity(self) -> None:
        """
        Validate aggregate integrity
        Should be called before publishing

        Raises:
            NoPassagesError: If test has no passages
            PassageCountMismatchError: If published test doesn't have correct passage count
        """
        if not self.passage_ids:
            raise NoPassagesError()

        required_passages = (
            FULL_TEST_PASSAGE_COUNT
            if self.test_type == TestType.FULL_TEST
            else SINGLE_PASSAGE_COUNT
        )

        if (
            self.status == TestStatus.PUBLISHED
            and len(self.passage_ids) != required_passages
        ):
            raise PassageCountMismatchError(
                self.test_type.value, required_passages, len(self.passage_ids)
            )
