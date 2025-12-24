from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.passage import Passage


class PassageRepository(ABC):
    @abstractmethod
    async def create(self, title: str, content: str, author_id: str):
        pass

    @abstractmethod
    async def get_by_id(self, passage_id: str) -> Optional[Passage]:
        pass

    @abstractmethod
    async def get_all(self) -> list[Passage]:
        pass
