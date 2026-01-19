from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.common.pagination import PaginatedResponse, SortableParams
from app.domain.aggregates.session import SessionStatus


class ParticipantSummaryDTO(BaseModel):
    student_id: str
    connection_status: str
    joined_at: Optional[datetime] = None


class SessionSummaryDTO(BaseModel):
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus
    participant_count: int
    created_by: str
    created_at: datetime


class ListSessionsQuery(SortableParams):
    teacher_id: Optional[str] = None
    class_id: Optional[str] = None


class ListSessionsResponse(PaginatedResponse[SessionSummaryDTO]):
    pass
