"""Text Highlight entity"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TextHighlight(BaseModel):
    """
    Represents a text highlight action by a student during a test.
    Stores full detail for analysis and persisting students' progress in case he disconnects.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime
    text: str  # The actual highlighted text
    passage_id: str
    position_start: int = Field(ge=0)  # Character position in passage
    position_end: int = Field(ge=0)
    color_code: str
    comment: Optional[str]

    def set_comment(self, comment: str):
        self.comment = comment if comment else None

    def clear_comment(self):
        self.comment = None

    def has_comment(self) -> bool:
        return self.comment is not None

    def set_color_code(self, color_code: str):
        self.color_code = color_code

    class Config:
        """Pydantic configuration"""

        frozen = False  # Allow updates to connection status and activity
