from dataclasses import dataclass


@dataclass
class SessionJoinRequest:
    session_id: str


@dataclass
class SessionJoinResponse:
    session_id: str
    participant_id: str
    success: bool
