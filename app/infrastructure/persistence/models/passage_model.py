from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastructure.persistence.models.base import BaseModel


class PassageModel(BaseModel):
    __tablename__ = "passages"

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    topic = Column(String(100), nullable=False)
    source = Column(String(255))
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("UserModel", back_populates="created_passages")
    questions = relationship(
        "QuestionModel", back_populates="passage", cascade="all, delete-orphan"
    )
    # Many-to-many relationship with tests will be handled through TestPassage association table
