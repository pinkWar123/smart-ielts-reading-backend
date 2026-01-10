from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.operators import or_

from app.domain.aggregates.users.user import User
from app.domain.repositories.user_repository import UserRepositoryInterface
from app.infrastructure.persistence.models import UserModel


class SqlUserRepositoryInterface(UserRepositoryInterface):

    async def get_by_id(self, user_id: str) -> Optional[UserModel]:
        query = select(UserModel).filter_by(id=user_id)
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return user_model

    async def find(self, username: str, email: str) -> Optional[User]:
        query = select(UserModel).filter(
            or_(UserModel.username == username, UserModel.email == email)
        )
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return self._to_domain_entity(user_model) if user_model else None

    async def get_by_username(self, username: str) -> Optional[User]:
        query = select(UserModel).filter_by(username=username)
        result = await self.session.execute(query)
        user_model = result.scalar_one_or_none()
        return self._to_domain_entity(user_model) if user_model else None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user: User) -> UserModel:
        user_model = UserModel(
            username=user.username,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role,
            full_name=user.full_name,
        )

        self.session.add(user_model)
        await self.session.commit()
        await self.session.refresh(user_model)
        return user_model

    async def get_by_password(self, username: str, password: str) -> Optional[User]:
        stmt = select(UserModel).filter_by(username=username, password_hash=password)
        result = await self.session.execute(stmt)
        user_model = result.scalar_one_or_none()
        return self._to_domain_entity(user_model) if user_model else None

    async def get_all(self) -> list[User]:
        stmt = select(UserModel)
        result = await self.session.execute(stmt)
        user_models = result.scalars().all()
        return [self._to_domain_entity(user_model) for user_model in user_models]

    def _to_domain_entity(self, user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            username=user_model.username,
            email=user_model.email,
            password_hash=user_model.password_hash,
            role=user_model.role,
            full_name=user_model.full_name,
            created_at=user_model.created_at,
            is_active=user_model.is_active,
        )
