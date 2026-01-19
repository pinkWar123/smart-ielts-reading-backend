from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.common.pagination import PaginatedResponse, SortableParams
from app.domain.aggregates.session import SessionStatus


class MySessionDTO(BaseModel):
    id: str
    class_id: str
    test_id: str
    title: str
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: SessionStatus
    my_attempt_id: Optional[str] = None
    my_joined_at: Optional[datetime] = None
    my_connection_status: str
    created_at: datetime


class GetMySessionsQuery(SortableParams):
    student_id: str


class GetMySessionsResponse(PaginatedResponse[MySessionDTO]):
    pass
