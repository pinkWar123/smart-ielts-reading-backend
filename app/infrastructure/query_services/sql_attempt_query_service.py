from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.query.attempts.attempt_query_model import AttemptDetail
from app.application.services.query.attempts.attempt_query_service import (
    AttemptQueryService,
)
from app.infrastructure.persistence.models import (
    AttemptModel,
    ClassModel,
    SessionModel,
    TestModel,
)


class SQLAttemptQueryService(AttemptQueryService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_attempt_by_id(self, attempt_id: str) -> AttemptDetail | None:
        stmt = (
            select(SessionModel, TestModel, ClassModel, AttemptModel)
            .select_from(AttemptModel)
            .outerjoin(SessionModel, SessionModel.id == AttemptModel.session_id)
            .outerjoin(TestModel, TestModel.id == SessionModel.test_id)
            .outerjoin(ClassModel, ClassModel.id == SessionModel.class_id)
            .where(AttemptModel.id == attempt_id)
        )

        result = await self.session.execute(stmt)
        row = result.one_or_none()

        if row is None:
            return None

        session_model: Optional[SessionModel]
        test_model: Optional[TestModel]
        class_model: Optional[ClassModel]
        attempt_model: Optional[AttemptModel]
        session_model, test_model, class_model, attempt_model = row

        if attempt_model is None:
            return None

        return AttemptDetail(
            id=attempt_model.id,
            started_at=attempt_model.started_at,
            status=attempt_model.status,
            submitted_at=attempt_model.submitted_at,
            time_remaining_seconds=attempt_model.time_remaining_seconds,
            answers=attempt_model.answers,
            tab_violations=attempt_model.tab_violations,
            highlighted_text=attempt_model.highlighted_text,
            current_passage_index=attempt_model.current_passage_index,
            current_question_index=attempt_model.current_question_index,
            test=test_model.to_domain() if test_model else None,
            session=session_model.to_domain() if session_model else None,
            class_=class_model.to_domain() if class_model else None,
            student_id=attempt_model.student_id,
        )
