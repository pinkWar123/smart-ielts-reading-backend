# app/domain/repositories/test_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entities.test import Test
from app.infrastructure.persistence.models import TestModel


class TestRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, test: Test) -> Test:
        pass

    @abstractmethod
    async def get_by_id(self, test_id: str) -> Optional[Test]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Test]:
        pass

    @abstractmethod
    async def update(self, test: Test) -> Test:
        pass

    @abstractmethod
    async def delete(self, test_id: str) -> bool:
        pass

    @abstractmethod
    async def is_passage_in_published_test(self, passage_id: str) -> bool:
        """Check if a passage is part of any published test"""
        pass
