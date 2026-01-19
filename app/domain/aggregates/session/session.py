"""Session Aggregate Root"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session.constants import (
    CONNECTION_STATUS_CONNECTED,
    CONNECTION_STATUS_DISCONNECTED,
    MAX_SESSION_TITLE_LENGTH,
    MIN_SESSION_TITLE_LENGTH,
)
from app.domain.aggregates.session.session_participant import SessionParticipant
from app.domain.aggregates.session.session_status import SessionStatus
from app.domain.errors.session_errors import (
    CannotCancelActiveSessionError,
    InvalidSessionStatusError,
    NoStudentsConnectedError,
    SessionNotJoinableError,
)


class Session(BaseModel):
    """
    Aggregate Root: Session (Exercise Session)

    Represents an exercise session where users take tests together in real-time.

    Business Rules:
    - Can only start if at least one student is connected
    - Cannot modify once IN_PROGRESS
    - Can only cancel if not IN_PROGRESS
    - Students can join during WAITING_FOR_STUDENTS or IN_PROGRESS
    - Global timer: started_at determines test end time for all users
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    class_id: str  # Reference to Class aggregate
    test_id: str  # Reference to Test aggregate
    title: str = Field(
        min_length=MIN_SESSION_TITLE_LENGTH, max_length=MAX_SESSION_TITLE_LENGTH
    )
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus = Field(default=SessionStatus.SCHEDULED)
    participants: List[SessionParticipant] = Field(default_factory=list)
    created_by: str  # Teacher ID who created the session
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    updated_at: Optional[datetime] = None

    def start_waiting_phase(self) -> None:
        """
        Open waiting room for users to join

        Business rules:
        - Can only transition from SCHEDULED status

        Raises:
            InvalidSessionStatusError: If session is not in SCHEDULED status
        """
        if self.status != SessionStatus.SCHEDULED:
            raise InvalidSessionStatusError(
                self.id, self.status, SessionStatus.SCHEDULED
            )

        self.status = SessionStatus.WAITING_FOR_STUDENTS
        self.updated_at = TimeHelper.utc_now()

    def student_join(self, student_id: str) -> None:
        """
        Student joins or reconnects to the session

        Business rules:
        - Can only join during WAITING_FOR_STUDENTS or IN_PROGRESS
        - If student already exists, update connection status
        - If new student, add to participants

        Args:
            student_id: ID of the student joining

        Raises:
            SessionNotJoinableError: If session is not joinable
        """
        if self.status not in [
            SessionStatus.WAITING_FOR_STUDENTS,
            SessionStatus.IN_PROGRESS,
        ]:
            raise SessionNotJoinableError(self.id, self.status)

        participant = self._get_participant(student_id)

        if participant:
            # Existing participant reconnecting
            participant.connection_status = CONNECTION_STATUS_CONNECTED
            participant.last_activity = TimeHelper.utc_now()
            if not participant.joined_at:
                participant.joined_at = TimeHelper.utc_now()
        else:
            # New participant
            new_participant = SessionParticipant(
                student_id=student_id,
                joined_at=TimeHelper.utc_now(),
                connection_status=CONNECTION_STATUS_CONNECTED,
                last_activity=TimeHelper.utc_now(),
            )
            self.participants.append(new_participant)

        self.updated_at = TimeHelper.utc_now()

    def student_disconnect(self, student_id: str) -> None:
        """
        Mark student as disconnected

        Args:
            student_id: ID of the student disconnecting
        """
        participant = self._get_participant(student_id)
        if participant:
            participant.connection_status = CONNECTION_STATUS_DISCONNECTED
            participant.last_activity = TimeHelper.utc_now()
            self.updated_at = TimeHelper.utc_now()

    def start_session(self) -> List[str]:
        """
        Start the test countdown - all connected users begin simultaneously

        Business rules:
        - Can only transition from WAITING_FOR_STUDENTS status
        - Must have at least one connected student

        Returns:
            List of student IDs who are connected and should have attempts created

        Raises:
            InvalidSessionStatusError: If session is not in WAITING_FOR_STUDENTS status
            NoStudentsConnectedError: If no users are connected
        """
        if self.status != SessionStatus.WAITING_FOR_STUDENTS:
            raise InvalidSessionStatusError(
                self.id, self.status, SessionStatus.WAITING_FOR_STUDENTS
            )

        connected_students = [
            p.student_id
            for p in self.participants
            if p.connection_status == CONNECTION_STATUS_CONNECTED
        ]

        if not connected_students:
            raise NoStudentsConnectedError(self.id)

        self.status = SessionStatus.IN_PROGRESS
        self.started_at = TimeHelper.utc_now()
        self.updated_at = TimeHelper.utc_now()

        return connected_students

    def link_attempt(self, student_id: str, attempt_id: str) -> None:
        """
        Link a created attempt to a participant

        Args:
            student_id: ID of the student
            attempt_id: ID of the created attempt
        """
        participant = self._get_participant(student_id)
        if participant:
            participant.attempt_id = attempt_id
            self.updated_at = TimeHelper.utc_now()

    def complete_session(self) -> None:
        """
        Mark session as completed

        Business rules:
        - Can only complete from IN_PROGRESS status

        Raises:
            InvalidSessionStatusError: If session is not IN_PROGRESS
        """
        if self.status != SessionStatus.IN_PROGRESS:
            raise InvalidSessionStatusError(
                self.id, self.status, SessionStatus.IN_PROGRESS
            )

        self.status = SessionStatus.COMPLETED
        self.completed_at = TimeHelper.utc_now()
        self.updated_at = TimeHelper.utc_now()

    def cancel_session(self) -> None:
        """
        Cancel the session before it starts

        Business rules:
        - Cannot cancel if session is IN_PROGRESS

        Raises:
            CannotCancelActiveSessionError: If session is currently IN_PROGRESS
        """
        if self.status == SessionStatus.IN_PROGRESS:
            raise CannotCancelActiveSessionError(self.id)

        self.status = SessionStatus.CANCELLED
        self.updated_at = TimeHelper.utc_now()

    def get_connected_student_count(self) -> int:
        """
        Get the number of currently connected users

        Returns:
            Number of connected users
        """
        return sum(
            1
            for p in self.participants
            if p.connection_status == CONNECTION_STATUS_CONNECTED
        )

    def is_student_in_session(self, student_id: str) -> bool:
        """
        Check if a student is a participant in this session

        Args:
            student_id: ID of the student to check

        Returns:
            True if student is a participant, False otherwise
        """
        return any(p.student_id == student_id for p in self.participants)

    def _get_participant(self, student_id: str) -> Optional[SessionParticipant]:
        """
        Get participant by student ID

        Args:
            student_id: ID of the student

        Returns:
            SessionParticipant if found, None otherwise
        """
        return next((p for p in self.participants if p.student_id == student_id), None)
