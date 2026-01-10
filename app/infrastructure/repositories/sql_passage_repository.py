from abc import abstractmethod
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.passage import Passage
from app.domain.repositories.passage_repository import PassageRepositoryInterface
from app.infrastructure.persistence.models import PassageModel as DBPassageModel


class SQLPassageRepositoryInterface(PassageRepositoryInterface):
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
        """
        Persist a domain aggregate to the database.

        DDD approach: The domain aggregate is already fully built in the domain layer.
        This method only maps domain entities → persistence models and persists.
        """
        # Map domain aggregate to persistence model
        passage_model = self._map_domain_to_persistence(passage)

        # Persist the complete aggregate (cascade handles children)
        self.session.add(passage_model)
        await self.session.commit()

        # Re-fetch to get DB-generated IDs and avoid lazy loading issues
        refreshed_passage_model = await self._fetch_passage_with_relations(passage.id)

        # Map back to domain entity
        return self._to_domain_entity_with_questions(refreshed_passage_model)

    def _map_domain_to_persistence(self, passage: Passage) -> DBPassageModel:
        """
        Map a complete domain Passage aggregate to persistence models.

        This is where the domain → infrastructure boundary crossing happens.
        """
        from app.infrastructure.persistence.models import (
            QuestionGroupModel,
            QuestionModel,
        )

        # Map passage (aggregate root)
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

        # Map question groups and track temporary ID → model mapping
        temp_id_to_qg_model = {}
        for qg in passage.question_groups:
            qg_model = QuestionGroupModel(
                passage_id=passage.id,
                group_instructions=qg.group_instructions,
                question_type=qg.question_type.value,
                start_question_number=qg.start_question_number,
                end_question_number=qg.end_question_number,
                order_in_passage=qg.order_in_passage,
                options=(
                    [opt.model_dump() for opt in qg.options] if qg.options else None
                ),
            )
            temp_id_to_qg_model[qg.id] = qg_model
            passage_model.question_groups.append(qg_model)

        # Map questions and establish relationships using object references
        for q in passage.questions:
            q_model = QuestionModel(
                passage_id=passage.id,
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

            # Resolve domain temporary ID to persistence model object reference
            if q.question_group_id and q.question_group_id in temp_id_to_qg_model:
                # Question belongs to a group - use object reference
                qg_model = temp_id_to_qg_model[q.question_group_id]
                qg_model.questions.append(q_model)
            else:
                # Standalone question
                passage_model.questions.append(q_model)

        return passage_model

    async def _fetch_passage_with_relations(self, passage_id: str) -> DBPassageModel:
        """Fetch passage with all relations eagerly loaded"""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(DBPassageModel)
            .options(
                selectinload(DBPassageModel.questions),
                selectinload(DBPassageModel.question_groups),
            )
            .filter_by(id=passage_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

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

    async def update_passage(self, passage: Passage) -> Passage:
        """
        Update an existing passage with new data.

        This method:
        1. Fetches the existing passage
        2. Deletes all existing questions and question groups
        3. Updates the passage fields
        4. Adds new questions and question groups

        This approach is more efficient than doing a complex diff and update.
        """
        from sqlalchemy import delete

        # Fetch existing passage
        stmt = select(DBPassageModel).filter_by(id=passage.id)
        result = await self.session.execute(stmt)
        passage_model = result.scalar_one_or_none()

        if not passage_model:
            from app.domain.errors.passage_errors import PassageNotFoundError

            raise PassageNotFoundError(passage.id)

        # Delete all existing question groups and questions for this passage
        # (cascade will handle orphaned questions)
        from app.infrastructure.persistence.models import (
            QuestionGroupModel,
            QuestionModel,
        )

        await self.session.execute(
            delete(QuestionGroupModel).where(
                QuestionGroupModel.passage_id == passage.id
            )
        )
        await self.session.execute(
            delete(QuestionModel).where(QuestionModel.passage_id == passage.id)
        )

        # Flush to ensure deletions are executed before we add new items
        await self.session.flush()

        # Expire the collections so they're reloaded as empty
        await self.session.refresh(passage_model, ["question_groups", "questions"])

        # Update passage fields
        passage_model.title = passage.title
        passage_model.content = passage.content
        passage_model.word_count = passage.word_count
        passage_model.difficulty_level = passage.difficulty_level
        passage_model.topic = passage.topic
        passage_model.source = passage.source
        passage_model.updated_at = passage.updated_at

        # Add new question groups and questions using existing mapping logic
        temp_id_to_qg_model = {}
        for qg in passage.question_groups:
            qg_model = QuestionGroupModel(
                passage_id=passage.id,
                group_instructions=qg.group_instructions,
                question_type=qg.question_type.value,
                start_question_number=qg.start_question_number,
                end_question_number=qg.end_question_number,
                order_in_passage=qg.order_in_passage,
                options=(
                    [opt.model_dump() for opt in qg.options] if qg.options else None
                ),
            )
            temp_id_to_qg_model[qg.id] = qg_model
            passage_model.question_groups.append(qg_model)

        # Add questions
        for q in passage.questions:
            q_model = QuestionModel(
                passage_id=passage.id,
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

            # Resolve domain temporary ID to persistence model object reference
            if q.question_group_id and q.question_group_id in temp_id_to_qg_model:
                qg_model = temp_id_to_qg_model[q.question_group_id]
                qg_model.questions.append(q_model)
            else:
                passage_model.questions.append(q_model)

        # Commit changes
        await self.session.commit()

        # Re-fetch to get updated state
        refreshed_passage_model = await self._fetch_passage_with_relations(passage.id)

        return self._to_domain_entity_with_questions(refreshed_passage_model)

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
                group_options = None
                if qg.options:
                    group_options = [Option(**opt) for opt in qg.options]

                question_groups.append(
                    QuestionGroup(
                        id=qg.id,
                        group_instructions=qg.group_instructions,
                        question_type=QuestionType(qg.question_type),
                        start_question_number=qg.start_question_number,
                        end_question_number=qg.end_question_number,
                        order_in_passage=qg.order_in_passage,
                        options=group_options,
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
