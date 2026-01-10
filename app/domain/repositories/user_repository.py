from abc import ABC, abstractmethod
from typing import Optional

from app.domain.aggregates.users.user import User
from app.infrastructure.persistence.models import UserModel


class UserRepositoryInterface(ABC):
    @abstractmethod
    async def create(self, user: User) -> UserModel:
        pass

    @abstractmethod
    async def get_by_password(self, username: str, password: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_all(self) -> list[User]:
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserModel]:
        pass

    @abstractmethod
    async def find(self, username: str, email: str) -> Optional[User]:
        pass
