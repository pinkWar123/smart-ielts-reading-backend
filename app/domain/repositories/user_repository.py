from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.passage import Passage
from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_by_password(self, username: str, password: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_all(self) -> list[User]:
        pass
