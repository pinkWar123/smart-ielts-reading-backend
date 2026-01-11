"""Session Participant Value Object"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.aggregates.session.constants import CONNECTION_STATUS_DISCONNECTED


class SessionParticipant(BaseModel):
    """
    Value Object: Session Participant

    Represents a student's participation in a session with connection metadata.

    This is a value object (not an entity) because:
    - It has no independent identity
    - It's always accessed in the context of a Session
    - It's immutable from the perspective of external actors
    """

    student_id: str
    attempt_id: Optional[str] = None  # Links to Attempt aggregate
    joined_at: Optional[datetime] = None
    connection_status: str = Field(default=CONNECTION_STATUS_DISCONNECTED)
    last_activity: Optional[datetime] = None

    class Config:
        """Pydantic configuration"""

        frozen = False  # Allow updates to connection status and activity
