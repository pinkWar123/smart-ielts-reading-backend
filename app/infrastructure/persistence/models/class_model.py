"""Class SQLAlchemy model"""

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.domain.aggregates.class_.class_status import ClassStatus
from app.infrastructure.persistence.models.base import BaseModel


class ClassModel(BaseModel):
    """
    SQLAlchemy model for teaching classes

    Optimizations:
    - student_ids stored as JSON array for fast membership checks
    - Indexed on teacher_id for fast teacher queries
    """

    __tablename__ = "classes"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    teacher_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    student_ids = Column(JSON, nullable=False, default=list)  # Array of student IDs
    status = Column(
        Enum(ClassStatus), default=ClassStatus.ACTIVE, nullable=False, index=True
    )
    updated_at = Column(DateTime(timezone=True))

    # Relationships
    teacher = relationship("UserModel", foreign_keys=[teacher_id])
    sessions = relationship(
        "SessionModel", back_populates="class_", cascade="all, delete-orphan"
    )

    def to_domain(self):
        """Convert ORM model to domain entity"""
        from app.domain.aggregates.class_ import Class

        return Class(
            id=self.id,
            name=self.name,
            description=self.description,
            teacher_id=self.teacher_id,
            student_ids=self.student_ids or [],
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
