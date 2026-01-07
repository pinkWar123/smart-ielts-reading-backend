import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.domain.aggregates.test import TestStatus, TestType
from app.infrastructure.persistence.models.base import Base, BaseModel

# Association table for many-to-many relationship between tests and passages
test_passages = Table(
    "test_passages",
    Base.metadata,
    Column("test_id", String, ForeignKey("tests.id"), primary_key=True),
    Column("passage_id", String, ForeignKey("passages.id"), primary_key=True),
    Column(
        "passage_order", Integer, nullable=False
    ),  # Order of passage in test (1, 2, 3)
)


class TestModel(BaseModel):
    __tablename__ = "tests"

    title = Column(String(200), nullable=False)
    description = Column(Text)
    test_type = Column(Enum(TestType), nullable=False)
    time_limit_minutes = Column(
        Integer, nullable=False
    )  # Usually 60 for full test, 20 for single passage
    total_questions = Column(Integer, nullable=False)
    total_points = Column(Integer, nullable=False)
    status = Column(Enum(TestStatus), default=TestStatus.DRAFT)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    creator = relationship("UserModel", back_populates="created_tests")
    attempts = relationship(
        "AttemptModel", back_populates="test", cascade="all, delete-orphan"
    )
    passages = relationship("PassageModel", secondary=test_passages, backref="tests")
