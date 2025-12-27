from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.orm import relationship

from app.domain.entities.user import User, UserRole
from app.infrastructure.persistence.models.base import BaseModel


class UserModel(BaseModel):
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(100), nullable=False)
    last_login = Column(DateTime, nullable=True)  # New column for testing migrations

    # Relationships
    created_tests = relationship(
        "TestModel", back_populates="creator", foreign_keys="[TestModel.created_by]"
    )
    created_passages = relationship(
        "PassageModel",
        back_populates="creator",
        foreign_keys="[PassageModel.created_by]",
    )
    attempts = relationship("AttemptModel", back_populates="student")
    refresh_tokens = relationship("RefreshTokenModel", back_populates="user")

    def to_domain(self):
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            role=self.role,
            full_name=self.full_name,
            password_hash=self.password_hash,
            created_at=self.created_at,
        )
