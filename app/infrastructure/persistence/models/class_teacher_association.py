"""Association table for many-to-many relationship between classes and teachers"""

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base import Base


class ClassTeacherAssociation(Base):
    """
    Association object for many-to-many relationship between classes and teachers

    Attributes:
        class_id: Foreign key to classes table
        teacher_id: Foreign key to users table
        assigned_at: Timestamp when teacher was assigned to the class
    """

    __tablename__ = "class_teachers"

    class_id = Column(
        String, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    teacher_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    assigned_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships to parent objects
    class_ = relationship("ClassModel", back_populates="teacher_associations")
    teacher = relationship("UserModel", back_populates="teaching_associations")
