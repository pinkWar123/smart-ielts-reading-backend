from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from app.domain.aggregates.session import SessionStatus


@dataclass
class StartWaitingPhaseRequest:
    session_id: str


@dataclass
class ParticipantDTO:
    student_id: str
    attempt_id: Optional[str]
    joined_at: Optional[datetime]
    connection_status: str
    last_activity: Optional[datetime]


@dataclass
class StartWaitingPhaseResponse:
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: SessionStatus
    participants: List[ParticipantDTO]
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
