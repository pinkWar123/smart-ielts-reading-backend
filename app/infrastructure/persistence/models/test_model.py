from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.domain.aggregates.test import Test, TestStatus, TestType
from app.infrastructure.persistence.models.base import Base, BaseModel


class TestPassageAssociation(Base):
    """Association object for many-to-many relationship between tests and passages"""

    __tablename__ = "test_passages"

    test_id = Column(String, ForeignKey("tests.id"), primary_key=True)
    passage_id = Column(String, ForeignKey("passages.id"), primary_key=True)
    passage_order = Column(
        Integer, nullable=False
    )  # Order of passage in test (1, 2, 3)

    # Relationships to parent objects
    test = relationship("TestModel", back_populates="passage_associations")
    passage = relationship("PassageModel")


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
    passage_associations = relationship(
        "TestPassageAssociation",
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="TestPassageAssociation.passage_order",
    )

    @property
    def passages(self):
        """Get passages in order"""
        return [assoc.passage for assoc in self.passage_associations]

    def to_domain(self) -> Test:
        return Test(
            id=self.id,
            title=self.title,
            description=self.description,
            test_type=self.test_type,
            time_limit_minutes=self.time_limit_minutes,
            total_questions=self.total_questions,
            total_points=self.total_points,
            status=self.status,
            created_by=self.creator.email,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
            passage_ids=[passage.id for passage in self.passages],
        )
