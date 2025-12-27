import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base import BaseModel


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    ABANDONED = "abandoned"


class AttemptModel(BaseModel):
    __tablename__ = "attempts"

    test_id = Column(String, ForeignKey("tests.id"), nullable=False)
    student_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)
    started_at = Column(DateTime(timezone=True), nullable=False)
    submitted_at = Column(DateTime(timezone=True))
    time_remaining_seconds = Column(Integer)
    answers = Column(JSON, default=list)
    tab_violations = Column(JSON, default=list)
    total_score = Column(Integer)
    percentage_score = Column(Float)
    current_passage_index = Column(Integer, default=0)
    current_question_index = Column(Integer, default=0)

    test = relationship("TestModel", back_populates="attempts")
    student = relationship("UserModel", back_populates="attempts")
