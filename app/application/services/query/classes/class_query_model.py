from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.application.services.common.user_dto import UserDto
from app.domain.aggregates.class_ import Class, ClassStatus
from app.domain.aggregates.users.user import User


class ClassSortField(str, Enum):
    """Fields that can be used to sort classes"""

    NAME = "name"
    CREATED_AT = "created_at"
    CREATED_BY = "created_by"
    STATUS = "status"


class ListClassStudentsQueryModel(BaseModel):
    id: str
    username: str
    email: str


class ListClassesQueryModel(BaseModel):
    id: str
    name: str
    description: str
    status: ClassStatus
    created_at: datetime
    created_by: User
    students: list[ListClassStudentsQueryModel]


class ClassDetailQueryModel(BaseModel):
    id: str
    name: str
    description: str
    status: ClassStatus
    created_at: datetime
    created_by: UserDto | None
    students: list[UserDto]
    teachers: list[UserDto]

    def to_domain(self):
        return Class(
            id=self.id,
            name=self.name,
            description=self.description,
            status=self.status,
            created_at=self.created_at,
            created_by=self.created_by.id,
            student_ids=[student.id for student in self.students],
            teacher_ids=[teacher.id for teacher in self.teachers],
        )
