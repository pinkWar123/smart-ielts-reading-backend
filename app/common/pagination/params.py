"""Pagination query parameters for API endpoints"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """
    Standard pagination query parameters.

    Use this as a dependency in FastAPI endpoints to handle pagination.
    """

    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-indexed)",
        examples=[1, 2, 3],
    )
    page_size: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of items per page (max 100)",
        examples=[10, 20, 50],
    )

    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.page_size

    def get_skip_limit(self) -> tuple[int, int]:
        """Get (skip, limit) tuple for database queries"""
        return self.offset, self.limit


class SortOrder(str, Enum):
    """Sort order enumeration"""

    ASC = "asc"
    DESC = "desc"


class SortableParams(PaginationParams):
    """
    Pagination with sorting support.

    Extend this class_ and override sort_by field with specific Enum for your use case.
    """

    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order (asc or desc)",
    )
