from dataclasses import dataclass
from datetime import datetime


@dataclass
class CompleteSessionRequest:
    session_id: str


@dataclass
class CompleteSessionResponse:
    session_id: str
    success: bool
    completed_at: datetime
    completed_by: str
