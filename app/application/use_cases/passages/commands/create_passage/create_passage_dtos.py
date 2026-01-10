from pydantic import BaseModel

from app.domain.aggregates.passage import Passage


class CreatePassageRequest(BaseModel):
    title: str
    content: str
    author_id: str


class PassageResponse(BaseModel):
    id: str
    title: str
    content: str
    word_count: int
    difficulty_level: int
    topic: str
    source: str | None
    created_by: str
    created_at: str
    updated_at: str | None
    is_active: bool

    @classmethod
    def from_entity(cls, passage: Passage) -> "PassageResponse":
        """Create a PassageResponse from a Passage domain entity."""
        return cls(
            id=passage.id,
            title=passage.title,
            content=passage.content,
            word_count=passage.word_count,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            created_by=passage.created_by,
            created_at=passage.created_at.isoformat(),
            updated_at=passage.updated_at.isoformat() if passage.updated_at else None,
            is_active=passage.is_active,
        )
