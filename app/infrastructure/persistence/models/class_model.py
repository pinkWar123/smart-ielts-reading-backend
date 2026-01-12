"""Class SQLAlchemy model"""

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.domain.aggregates.class_.class_status import ClassStatus
from app.infrastructure.persistence.models.base import BaseModel


class ClassModel(BaseModel):
    """
    SQLAlchemy model for teaching classes

    Relationships:
    - Many-to-many with teachers via class_teachers association table
    - Many-to-many with students via class_students association table
    - Indexed on status for filtering active/archived classes
    """

    __tablename__ = "classes"

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    status = Column(
        Enum(ClassStatus), default=ClassStatus.ACTIVE, nullable=False, index=True
    )
    updated_at = Column(DateTime(timezone=True))

    # Relationships
    sessions = relationship(
        "SessionModel", back_populates="class_", cascade="all, delete-orphan"
    )
    teacher_associations = relationship(
        "ClassTeacherAssociation", back_populates="class_", cascade="all, delete-orphan"
    )
    teachers = relationship(
        "UserModel",
        secondary="class_teachers",
        back_populates="taught_classes",
        viewonly=True,
    )
    student_associations = relationship(
        "ClassStudentAssociation", back_populates="class_", cascade="all, delete-orphan"
    )
    students = relationship(
        "UserModel",
        secondary="class_students",
        back_populates="enrolled_classes",
        viewonly=True,
    )

    def to_domain(self):
        """Convert ORM model to domain entity"""
        from app.domain.aggregates.class_ import Class

        return Class(
            id=self.id,
            name=self.name,
            description=self.description,
            teacher_ids=[assoc.teacher_id for assoc in self.teacher_associations],
            student_ids=[assoc.student_id for assoc in self.student_associations],
            status=self.status,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
