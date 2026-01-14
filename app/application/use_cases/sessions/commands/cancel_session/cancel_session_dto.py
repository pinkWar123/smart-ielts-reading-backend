from dataclasses import dataclass
from datetime import datetime


@dataclass
class CancelSessionRequest:
    session_id: str


@dataclass
class CancelSessionResponse:
    session_id: str
    success: bool
    cancelled_at: datetime
    cancelled_by: str
