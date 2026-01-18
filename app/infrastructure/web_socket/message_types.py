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


class ViolationRecordedMessage(BaseModel):
    type: Literal["violation"] = "violation"
    student_id: str
    violation_type: str
    timestamp: datetime
    total_count: int


# Student Activity Messages (Teacher Only)
class StudentProgressMessage(BaseModel):
    type: Literal["student_progress"] = "student_progress"
    session_id: str
    student_id: str
    student_name: str
    passage_index: int
    question_index: int
    question_number: int
    timestamp: datetime


class StudentAnswerMessage(BaseModel):
    type: Literal["student_answer"] = "student_answer"
    session_id: str
    student_id: str
    student_name: str
    question_id: str
    question_number: int
    answered: bool
    is_update: bool
    timestamp: datetime


class StudentHighlightMessage(BaseModel):
    type: Literal["student_highlight"] = "student_highlight"
    session_id: str
    student_id: str
    student_name: str
    text: str  # first 100 chars
    passage_id: str
    timestamp: datetime


class StudentSubmittedMessage(BaseModel):
    type: Literal["student_submitted"] = "student_submitted"
    session_id: str
    student_id: str
    student_name: str
    score: Optional[float]
    time_taken_seconds: int
    answered_questions: int
    total_questions: int
    timestamp: datetime


class SessionStatsMessage(BaseModel):
    type: Literal["session_stats"] = "session_stats"
    session_id: str
    stats: dict  # connection counts, progress, violations
    timestamp: datetime
