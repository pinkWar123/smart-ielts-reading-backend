from datetime import datetime
from enum import Enum

from pydantic import BaseModel

from app.domain.aggregates.class_ import ClassStatus
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
