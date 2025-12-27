from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.refresh_token import RefreshToken
from app.infrastructure.persistence.models.refresh_token_model import RefreshTokenModel


class RefreshTokenRepository(ABC):
    @abstractmethod
    def find(self, token: str) -> Optional[RefreshTokenModel]:
        pass

    @abstractmethod
    def create(self, refresh_token: RefreshToken) -> RefreshTokenModel:
        pass

    @abstractmethod
    def revoke(self, token: str) -> Optional[RefreshTokenModel]:
        pass
