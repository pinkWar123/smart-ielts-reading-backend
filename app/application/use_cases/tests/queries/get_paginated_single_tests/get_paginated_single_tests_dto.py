from typing import List, Optional

from pydantic import BaseModel

from app.common.pagination import PaginatedResponse, PaginationParams
from app.domain.aggregates.passage import QuestionType


class GetPaginatedSingleTestsQuery(PaginationParams):
    question_types: Optional[List[QuestionType]]


class TestDTO(BaseModel):
    id: str
    title: str
    question_types: List[QuestionType]


class GetPaginatedSingleTestsResponse(PaginatedResponse[TestDTO]):
    pass
