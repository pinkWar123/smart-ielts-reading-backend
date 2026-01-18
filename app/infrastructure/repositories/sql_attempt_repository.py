from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.aggregates.attempt.attempt import Attempt, AttemptStatus
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.infrastructure.persistence.models.attempt_model import (
    AttemptModel,
)
from app.infrastructure.persistence.models.attempt_model import (
    AttemptStatus as ModelAttemptStatus,
)


class SQLAttemptRepository(AttemptRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, attempt: Attempt) -> Attempt:
        """Create a new attempt"""
        attempt_model = AttemptModel(
            id=attempt.id,
            test_id=attempt.test_id,
            student_id=attempt.student_id,
            session_id=attempt.session_id,
            status=self._map_status_to_model(attempt.status),
            started_at=attempt.started_at,
            submitted_at=attempt.submitted_at,
            time_remaining_seconds=attempt.time_remaining_seconds,
            answers=self._serialize_answers(attempt.answers),
            tab_violations=self._serialize_violations(attempt.tab_violations),
            highlighted_text=self._serialize_highlights(attempt.highlighted_text),
            total_score=attempt.total_correct_answers,
            percentage_score=attempt.band_score,
            current_passage_index=attempt.current_passage_index,
            current_question_index=attempt.current_question_index,
        )
        self.session.add(attempt_model)
        await self.session.flush()
        await self.session.refresh(attempt_model)

        return attempt_model.to_domain()

    async def get_by_id(self, attempt_id: str) -> Optional[Attempt]:
        """Get an attempt by ID"""
        stmt = select(AttemptModel).where(AttemptModel.id == attempt_id)
        result = await self.session.execute(stmt)
        attempt_model = result.scalar_one_or_none()

        if attempt_model is None:
            return None

        return attempt_model.to_domain()

    async def get_by_student(self, student_id: str) -> List[Attempt]:
        """Get all attempts by a specific student"""
        stmt = (
            select(AttemptModel)
            .where(AttemptModel.student_id == student_id)
            .order_by(AttemptModel.started_at.desc())
        )
        result = await self.session.execute(stmt)
        attempt_models = result.scalars().all()

        return [model.to_domain() for model in attempt_models]

    async def get_by_test(self, test_id: str) -> List[Attempt]:
        """Get all attempts for a specific test"""
        stmt = (
            select(AttemptModel)
            .where(AttemptModel.test_id == test_id)
            .order_by(AttemptModel.started_at.desc())
        )
        result = await self.session.execute(stmt)
        attempt_models = result.scalars().all()

        return [model.to_domain() for model in attempt_models]

    async def get_by_session(self, session_id: str) -> List[Attempt]:
        """Get all attempts for a specific session"""
        stmt = (
            select(AttemptModel)
            .where(AttemptModel.session_id == session_id)
            .order_by(AttemptModel.started_at.desc())
        )
        result = await self.session.execute(stmt)
        attempt_models = result.scalars().all()

        return [model.to_domain() for model in attempt_models]

    async def get_by_student_and_test(
        self, student_id: str, test_id: str
    ) -> Optional[Attempt]:
        """Get a student's attempt for a specific test"""
        stmt = select(AttemptModel).where(
            AttemptModel.student_id == student_id, AttemptModel.test_id == test_id
        )
        result = await self.session.execute(stmt)
        attempt_model = result.scalar_one_or_none()

        if attempt_model is None:
            return None

        return attempt_model.to_domain()

    async def get_by_student_and_session(
        self, student_id: str, session_id: str
    ) -> Optional[Attempt]:
        """Get a student's attempt for a specific session"""
        stmt = select(AttemptModel).where(
            AttemptModel.student_id == student_id,
            AttemptModel.session_id == session_id,
        )
        result = await self.session.execute(stmt)
        attempt_model = result.scalar_one_or_none()

        if attempt_model is None:
            return None

        return attempt_model.to_domain()

    async def update(self, attempt: Attempt) -> Attempt:
        """Update an attempt"""
        stmt = select(AttemptModel).where(AttemptModel.id == attempt.id)
        result = await self.session.execute(stmt)
        attempt_model = result.scalar_one_or_none()

        if attempt_model is None:
            raise ValueError(f"Attempt with id {attempt.id} not found")

        # Update fields
        attempt_model.test_id = attempt.test_id
        attempt_model.student_id = attempt.student_id
        attempt_model.session_id = attempt.session_id
        attempt_model.status = self._map_status_to_model(attempt.status)
        attempt_model.started_at = attempt.started_at
        attempt_model.submitted_at = attempt.submitted_at
        attempt_model.time_remaining_seconds = attempt.time_remaining_seconds
        attempt_model.answers = self._serialize_answers(attempt.answers)
        attempt_model.tab_violations = self._serialize_violations(
            attempt.tab_violations
        )
        attempt_model.highlighted_text = self._serialize_highlights(
            attempt.highlighted_text
        )
        attempt_model.total_score = attempt.total_correct_answers
        attempt_model.percentage_score = attempt.band_score
        attempt_model.current_passage_index = attempt.current_passage_index
        attempt_model.current_question_index = attempt.current_question_index
        attempt_model.submit_type = attempt.submit_type

        await self.session.flush()
        await self.session.refresh(attempt_model)

        return attempt_model.to_domain()

    async def delete(self, attempt_id: str) -> bool:
        """Delete an attempt"""
        stmt = select(AttemptModel).where(AttemptModel.id == attempt_id)
        result = await self.session.execute(stmt)
        attempt_model = result.scalar_one_or_none()

        if attempt_model is None:
            return False

        await self.session.delete(attempt_model)
        await self.session.flush()

        return True

    async def get_in_progress_attempts_by_session(
        self, session_id: str
    ) -> List[Attempt]:
        """Get all in-progress attempts for a session"""
        stmt = (
            select(AttemptModel)
            .where(
                AttemptModel.session_id == session_id,
                AttemptModel.status == ModelAttemptStatus.IN_PROGRESS,
            )
            .order_by(AttemptModel.started_at.desc())
        )
        result = await self.session.execute(stmt)
        attempt_models = result.scalars().all()

        return [model.to_domain() for model in attempt_models]

    def _map_status_to_model(self, status: AttemptStatus) -> ModelAttemptStatus:
        """Map domain status to model status"""
        mapping = {
            AttemptStatus.IN_PROGRESS: ModelAttemptStatus.IN_PROGRESS,
            AttemptStatus.SUBMITTED: ModelAttemptStatus.SUBMITTED,
            AttemptStatus.ABANDONED: ModelAttemptStatus.ABANDONED,
        }
        return mapping[status]

    def _serialize_answers(self, answers) -> list:
        """Serialize answers to JSON-compatible format"""
        return [
            {
                "question_id": a.question_id,
                "student_answer": a.student_answer,
                "is_correct": a.is_correct,
                "points_earned": a.points_earned,
                "answered_at": a.answered_at.isoformat(),
            }
            for a in answers
        ]

    def _serialize_violations(self, violations) -> list:
        """Serialize violations to JSON-compatible format"""
        return [
            {
                "timestamp": v.timestamp.isoformat(),
                "violation_type": v.violation_type,
                "metadata": v.metadata,
            }
            for v in violations
        ]

    def _serialize_highlights(self, highlights) -> list:
        """Serialize highlights to JSON-compatible format"""
        return [
            {
                "id": h.id,
                "timestamp": h.timestamp.isoformat(),
                "text": h.text,
                "passage_id": h.passage_id,
                "position_start": h.position_start,
                "position_end": h.position_end,
                "color_code": h.color_code,
                "comment": h.comment,
            }
            for h in highlights
        ]
