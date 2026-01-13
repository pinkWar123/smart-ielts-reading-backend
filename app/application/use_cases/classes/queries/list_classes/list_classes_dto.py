from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.application.services.query.classes.class_query_model import ClassSortField
from app.common.pagination import PaginatedResponse, SortableParams, SortOrder
from app.domain.aggregates.class_ import ClassStatus


class ListClassesQuery(SortableParams):
    teacher_id: Optional[str] = None
    name: Optional[str] = None
    sort_by: Optional[ClassSortField] = Field(
        default=ClassSortField.CREATED_AT,
        description="Field to sort by (name, created_at, created_by, status)",
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC, description="Sort order (asc or desc)"
    )


class ClassCreatorDTO(BaseModel):
    id: str
    username: str


class ClassDTO(BaseModel):
    id: str
    name: str
    students_count: int
    description: Optional[str]
    status: ClassStatus
    created_at: datetime
    created_by: ClassCreatorDTO


class ListClassesResponse(PaginatedResponse[ClassDTO]):
    pass
