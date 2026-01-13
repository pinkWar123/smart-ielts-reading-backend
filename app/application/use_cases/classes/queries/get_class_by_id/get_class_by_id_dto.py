from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.application.services.common.user_dto import UserDto
from app.domain.aggregates.class_ import ClassStatus


class GetClassByIdQuery(BaseModel):
    id: str


class GetClassByIdResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: ClassStatus
    teachers: List[UserDto] = []
    students: List[UserDto] = []
    created_at: datetime
    created_by: UserDto
    updated_at: Optional[datetime] = None
