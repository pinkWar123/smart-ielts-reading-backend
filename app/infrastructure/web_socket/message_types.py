from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from app.domain.aggregates.session import SessionStatus


class HeartbeatMessage(BaseModel):
    type: Literal["heartbeat"] = "heartbeat"


class DisconnectMessage(BaseModel):
    type: Literal["disconnect"] = "disconnect"
    reason: Optional[str] = None


class ConnectedMessage(BaseModel):
    type: Literal["connected"] = "connected"
    session_id: str
    timestamp: datetime


class SessionStatusChangedMessage(BaseModel):
    type: Literal["session_status_changed"] = "session_status_changed"
    session_id: str
    status: SessionStatus
    timestamp: datetime


class ParticipantJoinedMessage(BaseModel):
    type: Literal["participant_joined"] = "participant_joined"
    session_id: str
    student_id: str
    connected_count: int
    timestamp: datetime


class ParticipantDisconnectedMessage(BaseModel):
    type: Literal["participant_disconnected"] = "participant_disconnected"
    session_id: str
    student_id: str
    connected_count: int
    timestamp: datetime


class WaitingRoomOpenedMessage(BaseModel):
    type: Literal["waiting_room_opened"] = "waiting_room_opened"
    session_id: str
    timestamp: datetime


class SessionStartedMessage(BaseModel):
    type: Literal["session_started"] = "session_started"
    session_id: str
    started_at: datetime
    connected_students: List[str]
    timestamp: datetime


class SessionCompletedMessage(BaseModel):
    type: Literal["session_completed"] = "session_completed"
    session_id: str
    completed_at: datetime
    timestamp: datetime


class ErrorMessage(BaseModel):
    type: Literal["error"] = "error"
    message: str
    code: str
