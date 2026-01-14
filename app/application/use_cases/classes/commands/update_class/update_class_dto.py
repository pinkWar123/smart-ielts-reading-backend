from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.domain.aggregates.class_.class_status import ClassStatus


class UpdateClassRequest(BaseModel):
    class_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ClassStatus] = None


class UpdateClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ClassStatus
    updated_at: datetime
