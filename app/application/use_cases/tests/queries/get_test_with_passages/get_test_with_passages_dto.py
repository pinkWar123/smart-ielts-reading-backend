from pydantic import BaseModel


class GetTestWithPassagesQuery(BaseModel):
    id: str


class PassageResponse(BaseModel):
    id: str
    title: str
    reduced_content: str
    word_count: int
    difficulty_level: int
    topic: str
    source: str | None
    created_by: str
    created_at: str
    updated_at: str | None


class GetTestWithPassagesResponse(BaseModel):
    id: str
    passage_count: int
    passages: list[PassageResponse]
