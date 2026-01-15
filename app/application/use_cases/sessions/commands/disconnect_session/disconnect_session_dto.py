from dataclasses import dataclass


@dataclass
class DisconnectSessionRequest:
    session_id: str


@dataclass
class DisconnectSessionResponse:
    session_id: str
    student_id: str
    success: bool
    connected_count: int
