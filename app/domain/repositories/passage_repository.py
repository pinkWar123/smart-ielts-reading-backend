from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.passage import Passage


class PassageRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, title: str, content: str, author_id: str):
        """Create a simple passage without questions (legacy method)"""
        pass

    @abstractmethod
    async def create_complete_passage(self, passage: Passage) -> Passage:
        """Create a complete passage with questions and question groups"""
        pass

    @abstractmethod
    async def get_by_id(self, passage_id: str) -> Optional[Passage]:
        """Get a passage by ID (without questions - lightweight)"""
        pass

    @abstractmethod
    async def get_by_id_with_questions(self, passage_id: str) -> Optional[Passage]:
        """Get a passage by ID with all questions and question groups"""
        pass

    @abstractmethod
    async def get_all(self) -> list[Passage]:
        pass

    @abstractmethod
    async def update_passage(self, passage: Passage) -> Passage:
        """Update an existing passage with new data"""
        pass
