from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.refresh_token import RefreshToken
from app.domain.repositories.refresh_token_repository import RefreshTokenRepository
from app.infrastructure.persistence.models.refresh_token_model import RefreshTokenModel


class SQLRefreshTokenRepository(RefreshTokenRepository):
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
