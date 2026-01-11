"""Class Aggregate Root"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.class_.class_status import ClassStatus
from app.domain.aggregates.class_.constants import (
    MAX_CLASS_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_CLASS_NAME_LENGTH,
)
from app.domain.errors.class_errors import (
    ClassAlreadyArchivedError,
    StudentAlreadyEnrolledError,
    StudentNotInClassError,
)


class Class(BaseModel):
    """
    Aggregate Root: Class (Teaching Class)

    Represents a teaching class_ (e.g., "Beacon 31") with enrolled students.

    Business Rules:
    - Student can only be enrolled into a class once
    - Cannot have duplicate student IDs
    - Can archive class_ if no longer active
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(
        min_length=MIN_CLASS_NAME_LENGTH, max_length=MAX_CLASS_NAME_LENGTH
    )
    description: Optional[str] = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    teacher_id: str  # Reference to User (ADMIN role)
    student_ids: List[str] = Field(
        default_factory=list
    )  # References to Users (STUDENT role)
    status: ClassStatus = Field(default=ClassStatus.ACTIVE)
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    updated_at: Optional[datetime] = None

    def enroll_student(self, student_id: str) -> None:
        """
        Add a student to the class_

        Business rules:
        - Student cannot yet be enrolled
        - Student ID must be valid (validated in use case layer)

        Args:
            student_id: ID of the student to enroll

        Raises:
            StudentAlreadyEnrolledError: If a student is already enrolled in this class_
        """
        if student_id in self.student_ids:
            raise StudentAlreadyEnrolledError(student_id, self.id)

        self.student_ids.append(student_id)
        self.updated_at = TimeHelper.utc_now()

    def remove_student(self, student_id: str) -> None:
        """
        Remove a student from the class_

        Args:
            student_id: ID of the student to remove

        Raises:
            StudentNotInClassError: If a student is not in this class_
        """
        if student_id not in self.student_ids:
            raise StudentNotInClassError(student_id, self.id)

        self.student_ids = [sid for sid in self.student_ids if sid != student_id]
        self.updated_at = TimeHelper.utc_now()

    def archive(self) -> None:
        """
        Archive the class_

        Business rules:
        - Cannot archive if already archived

        Raises:
            ClassAlreadyArchivedError: If class_ is already archived
        """
        if self.status == ClassStatus.ARCHIVED:
            raise ClassAlreadyArchivedError(self.id)

        self.status = ClassStatus.ARCHIVED
        self.updated_at = TimeHelper.utc_now()

    def is_student_enrolled(self, student_id: str) -> bool:
        """
        Check if a student is enrolled in this class_

        Args:
            student_id: ID of the student to check

        Returns:
            True if a student is enrolled, False otherwise
        """
        return student_id in self.student_ids

    def get_student_count(self) -> int:
        """
        Get the number of students enrolled in this class_

        Returns:
            Number of enrolled students
        """
        return len(self.student_ids)
