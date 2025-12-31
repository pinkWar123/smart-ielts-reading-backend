"""Test Aggregate Root"""

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.common.utils.time_helper import TimeHelper


class TestType(str, Enum):
    """IELTS Reading test types"""

    FULL_TEST = "FULL_TEST"  # 3 passages, ~40 questions, 60 minutes
    SINGLE_PASSAGE = "SINGLE_PASSAGE"  # 1 passage, ~13 questions, 20 minutes


class TestStatus(str, Enum):
    """Test lifecycle status"""

    DRAFT = "DRAFT"  # Being created/edited
    PUBLISHED = "PUBLISHED"  # Available for students
    ARCHIVED = "ARCHIVED"  # No longer active


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
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    test_type: TestType
    passage_ids: List[str] = Field(
        default_factory=list
    )  # References to Passage aggregates
    time_limit_minutes: int = Field(ge=1)
    total_questions: int = Field(ge=1)
    total_points: int = Field(ge=1)
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

        if test_type == TestType.FULL_TEST and len(v) > 3:
            raise ValueError("FULL_TEST cannot have more than 3 passages")
        elif test_type == TestType.SINGLE_PASSAGE and len(v) > 1:
            raise ValueError("SINGLE_PASSAGE cannot have more than 1 passage")

        return v

    def add_passage(self, passage_id: str) -> None:
        """
        Add a passage to the test

        Business rules:
        - Cannot add passages to published tests
        - Must respect passage count limits for test type
        """
        if self.status == TestStatus.PUBLISHED:
            raise ValueError("Cannot add passages to published test")

        if self.test_type == TestType.FULL_TEST and len(self.passage_ids) >= 3:
            raise ValueError("FULL_TEST can have maximum 3 passages")

        if self.test_type == TestType.SINGLE_PASSAGE and len(self.passage_ids) >= 1:
            raise ValueError("SINGLE_PASSAGE can have maximum 1 passage")

        if passage_id in self.passage_ids:
            raise ValueError(f"Passage {passage_id} already exists in test")

        self.passage_ids.append(passage_id)
        self.updated_at = TimeHelper.utc_now()

    def remove_passage(self, passage_id: str) -> None:
        """Remove a passage from the test"""
        if self.status == TestStatus.PUBLISHED:
            raise ValueError("Cannot remove passages from published test")

        self.passage_ids = [pid for pid in self.passage_ids if pid != passage_id]
        self.updated_at = TimeHelper.utc_now()

    def publish(self) -> None:
        """
        Publish the test

        Business rules:
        - Must have correct number of passages
        - Must be in DRAFT status
        """
        if self.status != TestStatus.DRAFT:
            raise ValueError("Only DRAFT tests can be published")

        required_passages = 3 if self.test_type == TestType.FULL_TEST else 1
        if len(self.passage_ids) != required_passages:
            raise ValueError(
                f"{self.test_type} requires exactly {required_passages} passage(s), "
                f"but has {len(self.passage_ids)}"
            )

        self.status = TestStatus.PUBLISHED
        self.updated_at = TimeHelper.utc_now()

    def archive(self) -> None:
        """Archive the test"""
        if self.status == TestStatus.ARCHIVED:
            raise ValueError("Test is already archived")

        self.status = TestStatus.ARCHIVED
        self.updated_at = TimeHelper.utc_now()

    def update_totals(self, total_questions: int, total_points: int) -> None:
        """
        Update total questions and points
        Should be called after passages are modified
        """
        if self.status == TestStatus.PUBLISHED:
            raise ValueError("Cannot update totals for published test")

        self.total_questions = total_questions
        self.total_points = total_points
        self.updated_at = TimeHelper.utc_now()

    def validate_integrity(self) -> None:
        """
        Validate aggregate integrity
        Should be called before publishing
        """
        if not self.passage_ids:
            raise ValueError("Test must have at least one passage")

        required_passages = 3 if self.test_type == TestType.FULL_TEST else 1
        if (
            self.status == TestStatus.PUBLISHED
            and len(self.passage_ids) != required_passages
        ):
            raise ValueError(
                f"Published {self.test_type} must have exactly {required_passages} passage(s)"
            )
