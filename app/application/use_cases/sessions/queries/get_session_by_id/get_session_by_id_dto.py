from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.session import SessionStatus


class ParticipantDetailDTO(BaseModel):
    student_id: str
    attempt_id: Optional[str] = None
    joined_at: Optional[datetime] = None
    connection_status: str
    last_activity: Optional[datetime] = None


class GetSessionByIdQuery(BaseModel):
    session_id: str


class GetSessionByIdResponse(BaseModel):
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus
    participants: List[ParticipantDetailDTO]
    connected_participant_count: int
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
