from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.aggregates.session import SessionStatus


class CreateSessionRequest(BaseModel):
    class_id: str = Field(description="ID of the class for this session")
    test_id: str = Field(description="ID of the test for this session")
    title: str = Field(
        description="Title of the session (e.g., 'Monday Morning Test')",
        min_length=3,
        max_length=200,
    )
    scheduled_at: datetime = Field(description="When the session is scheduled to start")


class ParticipantDTO(BaseModel):
    student_id: str
    attempt_id: Optional[str] = None
    joined_at: Optional[datetime] = None
    connection_status: str
    last_activity: Optional[datetime] = None


class CreateSessionResponse(BaseModel):
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    status: SessionStatus
    participants: List[ParticipantDTO]
    created_by: str
    created_at: datetime
