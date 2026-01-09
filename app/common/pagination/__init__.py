"""Pagination utilities for API responses"""

from app.common.pagination.dependencies import (
    get_pagination_params,
    get_sortable_params,
)
from app.common.pagination.helpers import (
    calculate_offset,
    create_paginated_response,
)
from app.common.pagination.params import (
    PaginationParams,
    SortableParams,
    SortOrder,
)
from app.common.pagination.response import (
    CursorPaginatedResponse,
    CursorPaginationMeta,
    PaginatedResponse,
    PaginationMeta,
)

__all__ = [
    # Query parameters
    "PaginationParams",
    "SortableParams",
    "SortOrder",
    # Response types
    "PaginatedResponse",
    "PaginationMeta",
    "CursorPaginatedResponse",
    "CursorPaginationMeta",
    # Helpers
    "create_paginated_response",
    "calculate_offset",
    # Dependencies
    "get_pagination_params",
    "get_sortable_params",
]
