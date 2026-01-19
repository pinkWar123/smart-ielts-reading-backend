from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.aggregates.class_ import ClassStatus
from app.domain.aggregates.class_.constants import (
    MAX_CLASS_NAME_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MIN_CLASS_NAME_LENGTH,
)


class CreateClassRequest(BaseModel):
    name: str = Field(
        description="Name of the class(e.g Beacon 31). Must be unique",
        max_length=MAX_CLASS_NAME_LENGTH,
        min_length=MIN_CLASS_NAME_LENGTH,
    )
    description: Optional[str] = Field(default=None, max_length=MAX_DESCRIPTION_LENGTH)
    teacher_ids: Optional[List[str]] = Field(
        description="IDs of teachers. At least one teacher required",
        default=list,
    )
    student_ids: Optional[list[str]] = Field(
        default_factory=list, description="IDs of users. Can be empty initially"
    )


class StudentDTO(BaseModel):
    id: str
    username: str
    full_name: str
    email: str


class TeacherDTO(BaseModel):
    id: str
    username: str
    full_name: str
    email: str


class CreateClassResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    status: ClassStatus
    teachers: List[TeacherDTO]
    students: List[StudentDTO] = []
