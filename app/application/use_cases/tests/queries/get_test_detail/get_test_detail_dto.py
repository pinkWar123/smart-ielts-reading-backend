
from typing import List

from pydantic import BaseModel

from app.application.use_cases.common.dtos.passage_detail_dto import PassageDTO, TestMetadata, UserView

class GetTestDetailResponse(BaseModel):
    """Complete extracted test response - ready to create passages and test"""

    passages: List[PassageDTO]
    test_metadata: TestMetadata


class GetTestDetailQuery(BaseModel):
    """Query to get a test detail"""

    id: str
    view: UserView
