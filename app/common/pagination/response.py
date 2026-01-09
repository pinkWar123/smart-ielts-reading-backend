"""Paginated response types"""

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata"""

    total_items: int = Field(description="Total number of items across all pages", ge=0)
    total_pages: int = Field(description="Total number of pages", ge=0)
    current_page: int = Field(description="Current page number (1-indexed)", ge=1)
    page_size: int = Field(description="Number of items per page", ge=1)
    has_next: bool = Field(description="Whether there is a next page")
    has_previous: bool = Field(description="Whether there is a previous page")

    @classmethod
    def from_params(
        cls, total_items: int, page: int, page_size: int
    ) -> "PaginationMeta":
        """
        Create pagination metadata from query parameters and total count.

        Args:
            total_items: Total number of items in the database
            page: Current page number (1-indexed)
            page_size: Number of items per page

        Returns:
            PaginationMeta object
        """
        total_pages = (
            (total_items + page_size - 1) // page_size if total_items > 0 else 0
        )

        return cls(
            total_items=total_items,
            total_pages=total_pages,
            current_page=page,
            page_size=page_size,
            has_next=page < total_pages,
            has_previous=page > 1,
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response structure.

    Type parameter T should be the DTO type for individual items.

    Example:
        ```python
        @router.get("", response_model=PaginatedResponse[TestDTO])
        async def get_tests(page: int = 1, page_size: int = 10):
            tests = await test_service.get_all(page, page_size)
            total = await test_service.count()

            return PaginatedResponse(
                data=tests,
                meta=PaginationMeta.from_params(total, page, page_size)
            )
        ```
    """

    data: List[T] = Field(description="List of items for current page")
    meta: PaginationMeta = Field(description="Pagination metadata")


class CursorPaginationMeta(BaseModel):
    """Cursor-based pagination metadata (for infinite scroll)"""

    has_next: bool = Field(description="Whether there are more items")
    next_cursor: Optional[str] = Field(
        None, description="Cursor for next page (if has_next is true)"
    )
    page_size: int = Field(description="Number of items per page", ge=1)


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """
    Generic cursor-paginated response structure.

    Use this for infinite scroll or when you need efficient pagination
    on large datasets without counting total items.

    Type parameter T should be the DTO type for individual items.
    """

    data: List[T] = Field(description="List of items for current page")
    meta: CursorPaginationMeta = Field(description="Cursor pagination metadata")
