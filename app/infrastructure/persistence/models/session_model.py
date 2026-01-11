"""Session SQLAlchemy model"""

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.domain.aggregates.session import SessionStatus
from app.infrastructure.persistence.models.base import BaseModel


class SessionModel(BaseModel):
    """
    SQLAlchemy model for exercise sessions

    Optimizations for fast writes and real-time visibility:
    - participants stored as JSON array for atomic updates
    - Indexed on class_id, status for fast filtering
    - Indexed on created_by for teacher queries
    - No cascade deletes to other tables (attempts are independent)
    """

    __tablename__ = "sessions"

    class_id = Column(String, ForeignKey("classes.id"), nullable=False, index=True)
    test_id = Column(String, ForeignKey("tests.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    status = Column(
        Enum(SessionStatus), default=SessionStatus.SCHEDULED, nullable=False, index=True
    )

    # Store participants as JSON for fast atomic updates
    # Structure: [{student_id, attempt_id, joined_at, connection_status, last_activity}, ...]
    participants = Column(JSON, nullable=False, default=list)

    created_by = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True))

    # Relationships
    class_ = relationship("ClassModel", back_populates="sessions")
    test = relationship("TestModel")
    creator = relationship("UserModel", foreign_keys=[created_by])
    attempts = relationship("AttemptModel", back_populates="session")

    def to_domain(self):
        """Convert ORM model to domain entity"""
        from datetime import datetime

        from app.domain.aggregates.session import Session, SessionParticipant

        # Convert JSON participants to SessionParticipant value objects
        participants_vos = []
        for p in self.participants or []:
            participants_vos.append(
                SessionParticipant(
                    student_id=p["student_id"],
                    attempt_id=p.get("attempt_id"),
                    joined_at=(
                        datetime.fromisoformat(p["joined_at"])
                        if p.get("joined_at")
                        else None
                    ),
                    connection_status=p.get("connection_status", "DISCONNECTED"),
                    last_activity=(
                        datetime.fromisoformat(p["last_activity"])
                        if p.get("last_activity")
                        else None
                    ),
                )
            )

        return Session(
            id=self.id,
            class_id=self.class_id,
            test_id=self.test_id,
            title=self.title,
            scheduled_at=self.scheduled_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            status=self.status,
            participants=participants_vos,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
