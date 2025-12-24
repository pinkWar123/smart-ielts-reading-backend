from abc import abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.passage import Passage
from app.domain.repositories.passage_repository import PassageRepository
from app.infrastructure.persistence.models import PassageModel as DBPassageModel


class SQLPassageRepository(PassageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Passage]:
        stmt = select(DBPassageModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_entity_(m) for m in models]

    async def create(self, title: str, content: str, author_id: str):
        # Calculate word count
        word_count = len(content.split()) if content else 0

        passage_model = DBPassageModel(
            title=title,
            content=content,
            word_count=word_count,
            difficulty_level=1,  # Default difficulty
            topic="General",  # Default topic, you may want to pass this as parameter
            created_by=author_id,
        )

        self.session.add(passage_model)
        await self.session.commit()
        await self.session.refresh(passage_model)

        return self._to_domain_entity_(passage_model)

    async def get_by_id(self, passage_id: str) -> Optional[Passage]:
        stmt = select(DBPassageModel).filter_by(id=passage_id)
        result = await self.session.execute(stmt)
        passage_model = result.scalar_one_or_none()
        if passage_model:
            return self._to_domain_entity_(passage_model)
        return None

    def _to_domain_entity_(self, passage_model: DBPassageModel) -> Passage:
        return Passage(
            id=passage_model.id,
            title=passage_model.title,
            content=passage_model.content,
            word_count=passage_model.word_count or 0,
            difficulty_level=passage_model.difficulty_level or 1,
            topic=passage_model.topic or "General",
            source=passage_model.source,
            created_by=passage_model.created_by,
            created_at=passage_model.created_at,
            updated_at=passage_model.updated_at,
        )
