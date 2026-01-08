from pydantic import BaseModel

from app.domain.aggregates.passage import Passage


class AuthorInfo(BaseModel):
    id: str
    username: str
    full_name: str
    email: str


class PassageDetail(Passage):
    created_by: AuthorInfo
