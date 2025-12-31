from abc import abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.passage import Passage
from app.domain.repositories.passage_repository import PassageRepository
from app.infrastructure.persistence.models import PassageModel as DBPassageModel


class SQLPassageRepository(PassageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[Passage]:
        stmt = select(DBPassageModel)
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain_entity_(m) for m in models]

    async def create(self, title: str, content: str, author_id: str):
        # Calculate word count
        word_count = len(content.split()) if content else 0

        passage_model = DBPassageModel(
            title=title,
            content=content,
            word_count=word_count,
            difficulty_level=1,  # Default difficulty
            topic="General",  # Default topic, you may want to pass this as parameter
            created_by=author_id,
        )

        self.session.add(passage_model)
        await self.session.commit()
        await self.session.refresh(passage_model)

        return self._to_domain_entity_(passage_model)

    async def create_complete_passage(self, passage: Passage) -> Passage:
        """Create a complete passage with questions and question groups"""
        from app.infrastructure.persistence.models import (
            QuestionGroupModel,
            QuestionModel,
        )

        # Validate passage integrity before persisting
        passage.validate_integrity()

        # Create passage model
        passage_model = DBPassageModel(
            id=passage.id,
            title=passage.title,
            content=passage.content,
            word_count=passage.word_count,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            created_by=passage.created_by,
            created_at=passage.created_at,
            updated_at=passage.updated_at,
            is_active=passage.is_active,
        )

        # Create question group models
        for qg in passage.question_groups:
            qg_model = QuestionGroupModel(
                id=qg.id,
                passage_id=passage.id,
                group_instructions=qg.group_instructions,
                question_type=qg.question_type.value,
                start_question_number=qg.start_question_number,
                end_question_number=qg.end_question_number,
                order_in_passage=qg.order_in_passage,
            )
            passage_model.question_groups.append(qg_model)

        # Create question models
        for q in passage.questions:
            q_model = QuestionModel(
                id=q.id,
                passage_id=passage.id,
                question_group_id=q.question_group_id,
                question_number=q.question_number,
                question_type=q.question_type.value,
                question_text=q.question_text,
                options=[opt.model_dump() for opt in q.options] if q.options else None,
                correct_answer=q.correct_answer.model_dump(),
                explanation=q.explanation,
                instructions=q.instructions,
                points=q.points,
                order_in_passage=q.order_in_passage,
            )
            passage_model.questions.append(q_model)

        # Persist to database
        self.session.add(passage_model)
        await self.session.commit()
        await self.session.refresh(passage_model)

        return self._to_domain_entity_with_questions(passage_model)

    async def get_by_id(self, passage_id: str) -> Optional[Passage]:
        stmt = select(DBPassageModel).filter_by(id=passage_id)
        result = await self.session.execute(stmt)
        passage_model = result.scalar_one_or_none()
        if passage_model:
            return self._to_domain_entity_(passage_model)
        return None

    async def get_by_id_with_questions(self, passage_id: str) -> Optional[Passage]:
        """Get a passage by ID with all its questions and question groups"""
        from sqlalchemy.orm import selectinload

        from app.infrastructure.persistence.models import (
            QuestionGroupModel,
            QuestionModel,
        )

        stmt = (
            select(DBPassageModel)
            .options(
                selectinload(DBPassageModel.questions),
                selectinload(DBPassageModel.question_groups),
            )
            .filter_by(id=passage_id)
        )
        result = await self.session.execute(stmt)
        passage_model = result.scalar_one_or_none()

        if not passage_model:
            return None

        return self._to_domain_entity_with_questions(passage_model)

    def _to_domain_entity_(self, passage_model: DBPassageModel) -> Passage:
        return Passage(
            id=passage_model.id,
            title=passage_model.title,
            content=passage_model.content,
            word_count=passage_model.word_count or 0,
            difficulty_level=passage_model.difficulty_level or 1,
            topic=passage_model.topic or "General",
            source=passage_model.source,
            created_by=passage_model.created_by,
            created_at=passage_model.created_at,
            updated_at=passage_model.updated_at,
        )

    def _to_domain_entity_with_questions(
        self, passage_model: DBPassageModel
    ) -> Passage:
        """Convert passage model to domain entity with questions and groups"""
        from app.domain.entities.question import Question, QuestionGroup, QuestionType
        from app.domain.value_objects.question_value_objects import (
            CorrectAnswer,
            Option,
        )

        # Convert question groups
        question_groups = []
        if passage_model.question_groups:
            for qg in passage_model.question_groups:
                question_groups.append(
                    QuestionGroup(
                        id=qg.id,
                        group_instructions=qg.group_instructions,
                        question_type=QuestionType(qg.question_type),
                        start_question_number=qg.start_question_number,
                        end_question_number=qg.end_question_number,
                        order_in_passage=qg.order_in_passage,
                    )
                )

        # Convert questions
        questions = []
        if passage_model.questions:
            for q in passage_model.questions:
                options = None
                if q.options:
                    options = [Option(**opt) for opt in q.options]

                questions.append(
                    Question(
                        id=q.id,
                        question_group_id=q.question_group_id,
                        question_number=q.question_number,
                        question_type=QuestionType(q.question_type),
                        question_text=q.question_text,
                        options=options,
                        correct_answer=CorrectAnswer(**q.correct_answer),
                        explanation=q.explanation,
                        instructions=q.instructions,
                        points=q.points,
                        order_in_passage=q.order_in_passage,
                    )
                )

        return Passage(
            id=passage_model.id,
            title=passage_model.title,
            content=passage_model.content,
            word_count=passage_model.word_count or 0,
            difficulty_level=passage_model.difficulty_level or 1,
            topic=passage_model.topic or "General",
            source=passage_model.source,
            created_by=passage_model.created_by,
            created_at=passage_model.created_at,
            updated_at=passage_model.updated_at,
            question_groups=question_groups,
            questions=questions,
        )
