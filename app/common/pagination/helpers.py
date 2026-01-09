"""Helper functions for pagination"""

from typing import List, TypeVar

from app.common.pagination.response import PaginatedResponse, PaginationMeta

T = TypeVar("T")


def create_paginated_response(
    items: List[T],
    total_items: int,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    """
    Create a paginated response from a list of items.

    Args:
        items: List of items for current page
        total_items: Total number of items in the database
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        PaginatedResponse with data and metadata

    Example:
        ```python
        # In your use case or repository
        items = await repository.get_all(skip=offset, limit=limit)
        total = await repository.count()

        return create_paginated_response(
            items=items,
            total_items=total,
            page=page,
            page_size=page_size,
        )
        ```
    """
    meta = PaginationMeta.from_params(
        total_items=total_items,
        page=page,
        page_size=page_size,
    )

    return PaginatedResponse(data=items, meta=meta)


def calculate_offset(page: int, page_size: int) -> int:
    """
    Calculate database offset from page number.

    Args:
        page: Current page number (1-indexed)
        page_size: Number of items per page

    Returns:
        Offset for database query
    """
    return (page - 1) * page_size
