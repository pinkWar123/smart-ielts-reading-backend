from abc import ABC, abstractmethod
from typing import Optional

from app.application.services.query.classes.class_query_model import (
    ClassDetailQueryModel,
    ClassSortField,
    ListClassesQueryModel,
)
from app.common.pagination import PaginatedResponse, SortOrder


class ClassQueryService(ABC):
    @abstractmethod
    async def list_classes(
        self,
        page: int,
        page_size: int,
        sort_by: Optional[ClassSortField],
        sort_order: Optional[SortOrder],
        teacher_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> PaginatedResponse[ListClassesQueryModel]:
        pass

    @abstractmethod
    async def get_class_by_id(self, class_id: str) -> Optional[ClassDetailQueryModel]:
        pass
