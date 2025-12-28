# app/domain/repositories/question_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.question import Question


class QuestionRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def get_by_id(self, question_id: str) -> Optional[Question]:
        pass

    @abstractmethod
    async def get_by_passage_id(self, passage_id: str) -> List[Question]:
        pass

    @abstractmethod
    async def update(self, question: Question) -> Question:
        pass

    @abstractmethod
    async def delete(self, question_id: str) -> bool:
        pass
