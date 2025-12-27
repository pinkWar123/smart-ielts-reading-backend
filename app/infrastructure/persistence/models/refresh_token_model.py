from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.common.utils.time_helper import TimeHelper
from app.infrastructure.persistence.models.base import BaseModel


class RefreshTokenModel(BaseModel):
    __tablename__ = "refresh_tokens"

    token = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    issued_at = Column(
        DateTime(timezone=True), nullable=False, default=TimeHelper.utc_now
    )
    expires_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False, nullable=False)

    user = relationship("UserModel", back_populates="refresh_tokens")
