from pydantic import BaseModel

from app.common.pagination import PaginatedResponse, PaginationParams


class GetPaginatedFullTestsQuery(PaginationParams):
    pass


class FullTestDTO(BaseModel):
    id: str
    title: str


class GetPaginatedFullTestsResponse(PaginatedResponse[FullTestDTO]):
    pass
