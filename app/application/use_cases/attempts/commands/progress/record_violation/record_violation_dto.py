from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.domain.aggregates.attempt.violation_type import ViolationType


class RecordViolationRequest(BaseModel):
    attempt_id: str
    violation_type: ViolationType = Field(
        ..., description="Type of violation being recorded"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional additional context (e.g., tab title, url)",
    )


class RecordViolationResponse(BaseModel):
    violation_type: str
    timestamp: datetime
    total_violations: int
