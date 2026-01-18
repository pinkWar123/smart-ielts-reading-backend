from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RecordHighlightRequest(BaseModel):
    attempt_id: str
    text: str = Field(
        ..., min_length=1, max_length=5000, description="The highlighted text"
    )
    passage_id: str = Field(..., description="ID of the passage containing the text")
    position_start: int = Field(..., ge=0, description="Start position in the passage")
    position_end: int = Field(..., gt=0, description="End position in the passage")
    color: Optional[str] = Field(
        default="yellow", description="Highlight color (for future multi-color support)"
    )

    def model_post_init(self, __context):
        """Validate that position_end > position_start"""
        if self.position_end <= self.position_start:
            raise ValueError("position_end must be greater than position_start")


class RecordHighlightResponse(BaseModel):
    id: str
    text: str
    passage_id: str
    position_start: int
    position_end: int
    color: str
    timestamp: datetime
