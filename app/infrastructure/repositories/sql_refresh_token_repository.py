from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import (
    RefreshTokenRepositoryInterface,
)
from app.infrastructure.persistence.models import UserModel
from app.infrastructure.persistence.models.refresh_token_model import RefreshTokenModel


class SQLRefreshTokenRepositoryInterface(RefreshTokenRepositoryInterface):
    async def get_user_by_token(self, token: str) -> Optional[UserModel]:
        query = (
            select(UserModel)
            .join(RefreshTokenModel)
            .filter(RefreshTokenModel.token == token)
        )
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return user_model

    async def revoke_active_tokens_by_user(self, user_id: str) -> None:
        query = (
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        await self.session.execute(query)
        await self.session.commit()

    async def get_active_tokens(self, user_id: str) -> List[RefreshTokenModel]:
        query = select(RefreshTokenModel).filter_by(user_id=user_id, revoked=False)
        result = await self.session.execute(query)
        token_models = list(result.scalars().all())
        return token_models

    async def revoke(self, token: str) -> Optional[RefreshTokenModel]:
        refresh_token_model = await self.find(token)
        if not refresh_token_model:
            return None
        refresh_token_model.revoked = True
        await self.session.commit()
        await self.session.refresh(refresh_token_model)
        return refresh_token_model

    async def create(self, token_model: RefreshToken) -> RefreshTokenModel:
        refresh_toke_model = RefreshTokenModel(
            token=token_model.token,
            user_id=token_model.user_id,
            issued_at=token_model.issued_at,
            expires_at=token_model.expires_at,
            revoked=False,
        )
        self.session.add(refresh_toke_model)
        await self.session.commit()
        await self.session.refresh(refresh_toke_model)
        return refresh_toke_model

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find(self, token: str) -> Optional[RefreshTokenModel]:
        query = select(RefreshTokenModel).filter_by(token=token)
        result = await self.session.execute(query)
        token_model = result.scalar_one_or_none()
        return token_model
