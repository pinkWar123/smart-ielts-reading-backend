"""FastAPI dependencies for pagination"""

from fastapi import Query

from app.common.pagination.params import PaginationParams, SortableParams, SortOrder


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of items per page (max 100)"
    ),
) -> PaginationParams:
    """
    FastAPI dependency for pagination parameters.

    Usage in endpoint:
        ```python
        @router.get("")
        async def get_items(
            pagination: PaginationParams = Depends(get_pagination_params)
        ):
            items = await repository.get_all(
                skip=pagination.offset,
                limit=pagination.limit
            )
            ...
        ```
    """
    return PaginationParams(page=page, page_size=page_size)


def get_sortable_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of items per page (max 100)"
    ),
    sort_by: str = Query(None, description="Field to sort by"),
    sort_order: SortOrder = Query(
        SortOrder.DESC, description="Sort order (asc or desc)"
    ),
) -> SortableParams:
    """
    FastAPI dependency for sortable pagination parameters.

    Usage in endpoint:
        ```python
        @router.get("")
        async def get_items(
            pagination: SortableParams = Depends(get_sortable_params)
        ):
            items = await repository.get_all(
                skip=pagination.offset,
                limit=pagination.limit,
                sort_by=pagination.sort_by,
                sort_order=pagination.sort_order
            )
            ...
        ```
    """
    return SortableParams(
        page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order
    )
