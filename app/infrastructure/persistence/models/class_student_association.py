"""Association table for many-to-many relationship between classes and users"""

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base import Base


class ClassStudentAssociation(Base):
    """
    Association object for many-to-many relationship between classes and users

    Attributes:
        class_id: Foreign key to classes table
        student_id: Foreign key to users table
        enrolled_at: Timestamp when student was enrolled in the class
    """

    __tablename__ = "class_students"

    class_id = Column(
        String, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    student_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    enrolled_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships to parent objects
    class_ = relationship("ClassModel", back_populates="student_associations")
    student = relationship("UserModel", back_populates="class_associations")
