from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.aggregates.session import Session, SessionStatus
from app.domain.repositories.session_repository import SessionRepositoryInterface
from app.infrastructure.persistence.models import SessionModel


class SQLSessionRepository(SessionRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, session_entity: Session) -> Session:
        """Create a new session"""
        session_model = SessionModel(
            id=session_entity.id,
            class_id=session_entity.class_id,
            test_id=session_entity.test_id,
            title=session_entity.title,
            scheduled_at=session_entity.scheduled_at,
            started_at=session_entity.started_at,
            completed_at=session_entity.completed_at,
            status=session_entity.status,
            participants=self._serialize_participants(session_entity.participants),
            created_by=session_entity.created_by,
            created_at=session_entity.created_at,
            updated_at=session_entity.updated_at,
        )
        self.session.add(session_model)
        await self.session.flush()
        await self.session.refresh(session_model)

        return session_model.to_domain()

    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        stmt = (
            select(SessionModel)
            .where(SessionModel.id == session_id)
            .options(
                selectinload(SessionModel.class_),
                selectinload(SessionModel.test),
                selectinload(SessionModel.creator),
            )
        )
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model is None:
            return None

        return session_model.to_domain()

    async def get_by_class(self, class_id: str) -> List[Session]:
        """Get all sessions for a specific class"""
        stmt = (
            select(SessionModel)
            .where(SessionModel.class_id == class_id)
            .options(
                selectinload(SessionModel.class_),
                selectinload(SessionModel.test),
                selectinload(SessionModel.creator),
            )
            .order_by(SessionModel.scheduled_at.desc())
        )
        result = await self.session.execute(stmt)
        session_models = result.scalars().all()

        return [model.to_domain() for model in session_models]

    async def get_by_student(self, student_id: str) -> List[Session]:
        """Get all sessions where a student is a participant"""
        stmt = (
            select(SessionModel)
            .options(
                selectinload(SessionModel.class_),
                selectinload(SessionModel.test),
                selectinload(SessionModel.creator),
            )
            .order_by(SessionModel.scheduled_at.desc())
        )
        result = await self.session.execute(stmt)
        all_sessions = result.scalars().all()

        # Filter sessions where student is a participant
        student_sessions = [
            model.to_domain()
            for model in all_sessions
            if any(
                p.get("student_id") == student_id for p in (model.participants or [])
            )
        ]

        return student_sessions

    async def get_by_teacher(self, teacher_id: str) -> List[Session]:
        """Get all sessions created by a specific teacher"""
        stmt = (
            select(SessionModel)
            .where(SessionModel.created_by == teacher_id)
            .options(
                selectinload(SessionModel.class_),
                selectinload(SessionModel.test),
                selectinload(SessionModel.creator),
            )
            .order_by(SessionModel.scheduled_at.desc())
        )
        result = await self.session.execute(stmt)
        session_models = result.scalars().all()

        return [model.to_domain() for model in session_models]

    async def update(self, session_entity: Session) -> Session:
        """Update a session"""
        stmt = select(SessionModel).where(SessionModel.id == session_entity.id)
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model is None:
            raise ValueError(f"Session with id {session_entity.id} not found")

        # Update fields
        session_model.class_id = session_entity.class_id
        session_model.test_id = session_entity.test_id
        session_model.title = session_entity.title
        session_model.scheduled_at = session_entity.scheduled_at
        session_model.started_at = session_entity.started_at
        session_model.completed_at = session_entity.completed_at
        session_model.status = session_entity.status
        session_model.participants = self._serialize_participants(
            session_entity.participants
        )
        session_model.updated_at = session_entity.updated_at

        await self.session.flush()
        await self.session.refresh(session_model)

        return session_model.to_domain()

    async def delete(self, session_id: str) -> bool:
        """Delete a session"""
        stmt = select(SessionModel).where(SessionModel.id == session_id)
        result = await self.session.execute(stmt)
        session_model = result.scalar_one_or_none()

        if session_model is None:
            return False

        await self.session.delete(session_model)
        await self.session.flush()

        return True

    async def get_active_sessions(self) -> List[Session]:
        """Get all active sessions (WAITING_FOR_STUDENTS or IN_PROGRESS)"""
        stmt = (
            select(SessionModel)
            .where(
                SessionModel.status.in_(
                    [SessionStatus.WAITING_FOR_STUDENTS, SessionStatus.IN_PROGRESS]
                )
            )
            .options(
                selectinload(SessionModel.class_),
                selectinload(SessionModel.test),
                selectinload(SessionModel.creator),
            )
            .order_by(SessionModel.scheduled_at.desc())
        )
        result = await self.session.execute(stmt)
        session_models = result.scalars().all()

        return [model.to_domain() for model in session_models]

    def _serialize_participants(self, participants) -> list:
        """Serialize participants to JSON-compatible format"""
        return [
            {
                "student_id": p.student_id,
                "attempt_id": p.attempt_id,
                "joined_at": p.joined_at.isoformat() if p.joined_at else None,
                "connection_status": p.connection_status,
                "last_activity": (
                    p.last_activity.isoformat() if p.last_activity else None
                ),
            }
            for p in participants
        ]
