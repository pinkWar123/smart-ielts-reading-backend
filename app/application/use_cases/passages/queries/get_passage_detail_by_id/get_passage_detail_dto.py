from pydantic import BaseModel

from app.application.services.query.passages.passages_query_model import AuthorInfo
from app.application.use_cases.common.dtos.passage_detail_dto import PassageDTO


class GetPassageDetailByIdQuery(BaseModel):
    id: str


class GetPassageDetailByIdResponse(PassageDTO):
    created_by: AuthorInfo
