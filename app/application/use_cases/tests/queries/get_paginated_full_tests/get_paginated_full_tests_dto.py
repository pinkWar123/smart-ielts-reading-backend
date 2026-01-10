from pydantic import BaseModel

from app.common.pagination import PaginatedResponse, PaginationParams
from app.domain.aggregates.test import TestStatus


class GetPaginatedFullTestsQuery(PaginationParams):
    status: TestStatus
    pass


class FullTestDTO(BaseModel):
    id: str
    title: str


class GetPaginatedFullTestsResponse(PaginatedResponse[FullTestDTO]):
    pass
