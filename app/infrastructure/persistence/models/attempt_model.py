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

    def to_domain(self):
        """Convert ORM model to domain entity"""
        from datetime import datetime

        from app.domain.aggregates.attempt.attempt import (
            Answer,
            Attempt,
        )
        from app.domain.aggregates.attempt.attempt import (
            AttemptStatus as DomainAttemptStatus,
        )
        from app.domain.aggregates.attempt.attempt import (
            TabViolation,
        )
        from app.domain.aggregates.attempt.text_highlight import TextHighlight

        # Convert JSON data to domain value objects
        answers_vos = [
            Answer(
                question_id=a["question_id"],
                student_answer=a["student_answer"],
                is_correct=a["is_correct"],
                points_earned=a.get("points_earned", 0),
                answered_at=datetime.fromisoformat(a["answered_at"]),
            )
            for a in (self.answers or [])
        ]

        tab_violations_vos = [
            TabViolation(
                timestamp=datetime.fromisoformat(v["timestamp"]),
                violation_type=v["violation_type"],
                metadata=v.get("metadata"),
            )
            for v in (self.tab_violations or [])
        ]

        highlighted_text_vos = [
            TextHighlight(
                id=h.get("id"),
                timestamp=datetime.fromisoformat(h["timestamp"]),
                text=h["text"],
                passage_id=h["passage_id"],
                position_start=h["position_start"],
                position_end=h["position_end"],
                color_code=h.get("color_code", "#FFFF00"),
                comment=h.get("comment"),
            )
            for h in (self.highlighted_text or [])
        ]

        # Map database enum to domain enum
        status_mapping = {
            AttemptStatus.IN_PROGRESS: DomainAttemptStatus.IN_PROGRESS,
            AttemptStatus.SUBMITTED: DomainAttemptStatus.SUBMITTED,
            AttemptStatus.ABANDONED: DomainAttemptStatus.ABANDONED,
        }

        return Attempt(
            id=self.id,
            test_id=self.test_id,
            student_id=self.student_id,
            session_id=self.session_id,
            status=status_mapping[self.status],
            started_at=self.started_at,
            submitted_at=self.submitted_at,
            time_remaining_seconds=self.time_remaining_seconds,
            answers=answers_vos,
            tab_violations=tab_violations_vos,
            highlighted_text=highlighted_text_vos,
            total_correct_answers=self.total_score,
            band_score=self.percentage_score,
            current_passage_index=self.current_passage_index,
            current_question_index=self.current_question_index,
        )
