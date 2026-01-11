import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base import BaseModel


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


class AttemptModel(BaseModel):
    """
    SQLAlchemy model for student test attempts

    Optimizations for fast writes during active sessions:
    - JSON columns for answers, violations, highlights (atomic updates)
    - Indexed on session_id, student_id, status for fast queries
    - Minimal constraints for maximum write speed
    """

    __tablename__ = "attempts"

    test_id = Column(String, ForeignKey("tests.id"), nullable=False, index=True)
    student_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(
        String, ForeignKey("sessions.id"), nullable=True, index=True
    )  # NEW: Link to session
    status = Column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    time_remaining_seconds = Column(Integer)

    # JSON arrays for fast atomic updates
    answers = Column(JSON, default=list)
    tab_violations = Column(JSON, default=list)
    highlighted_text = Column(
        JSON, default=list
    )  # NEW: Text highlights with full detail

    total_score = Column(Integer)
    percentage_score = Column(Float)
    current_passage_index = Column(Integer, default=0)
    current_question_index = Column(Integer, default=0)

    # Relationships
    test = relationship("TestModel", back_populates="attempts")
    student = relationship("UserModel", back_populates="attempts")
    session = relationship("SessionModel", back_populates="attempts")  # NEW
