import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Passage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    word_count: int = Field(ge=0)
    difficulty_level: int = Field(ge=1, le=5)
    topic: str = Field(min_length=1, max_length=255)
    source: Optional[str]
    created_by: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    is_active: bool = True
