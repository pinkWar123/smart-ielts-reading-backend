"""Session status enumeration"""

from enum import Enum


class SessionStatus(str, Enum):
    """Exercise session lifecycle status"""

    SCHEDULED = "SCHEDULED"  # Created but not started
    WAITING_FOR_STUDENTS = "WAITING_FOR_STUDENTS"  # Waiting room is open
    IN_PROGRESS = "IN_PROGRESS"  # Test countdown is active
    COMPLETED = "COMPLETED"  # Session finished
    CANCELLED = "CANCELLED"  # Session was cancelled
