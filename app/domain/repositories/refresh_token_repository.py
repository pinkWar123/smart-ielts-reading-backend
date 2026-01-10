from abc import ABC, abstractmethod
from typing import Optional

from app.domain.aggregates.users.refresh_token import RefreshToken
from app.infrastructure.persistence.models import UserModel
from app.infrastructure.persistence.models.refresh_token_model import RefreshTokenModel


class RefreshTokenRepositoryInterface(ABC):
    @abstractmethod
    async def find(self, token: str) -> Optional[RefreshTokenModel]:
        pass

    @abstractmethod
    async def create(self, refresh_token: RefreshToken) -> RefreshTokenModel:
        pass

    @abstractmethod
    async def revoke(self, token: str) -> Optional[RefreshTokenModel]:
        pass

    @abstractmethod
    async def get_active_tokens(self, user_id: str) -> list[RefreshTokenModel]:
        pass

    @abstractmethod
    async def revoke_active_tokens_by_user(self, user_id: str) -> None:
        pass

    @abstractmethod
    async def get_user_by_token(self, token: str) -> Optional[UserModel]:
        pass
