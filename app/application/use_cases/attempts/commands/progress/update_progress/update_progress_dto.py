from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UpdateProgressRequest(BaseModel):
    attempt_id: str
    passage_index: int = Field(ge=0, description="Current passage index (0-based)")
    question_index: int = Field(ge=0, description="Current question index (0-based)")
    passage_id: Optional[str] = Field(
        None, description="Optional passage ID for validation"
    )
    question_id: Optional[str] = Field(
        None, description="Optional question ID for validation"
    )


class UpdateProgressResponse(BaseModel):
    passage_index: int
    question_index: int
    updated_at: datetime
