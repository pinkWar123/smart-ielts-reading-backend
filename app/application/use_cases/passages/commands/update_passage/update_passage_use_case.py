"""Update Passage Use Case"""

from app.application.use_cases.passages.commands.update_passage.update_passage_dto import (
    UpdatePassageRequest,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.passage import Passage, Question, QuestionGroup
from app.domain.errors.passage_errors import (
    PassageInPublishedTestError,
    PassageNotFoundError,
)
from app.domain.repositories.passage_repository import PassageRepositoryInterface
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option


class UpdatePassageUseCase:
    """Use case for updating an existing passage"""

    def __init__(
        self,
        passage_repository: PassageRepositoryInterface,
        test_repository: TestRepositoryInterface,
    ):
        self.passage_repository = passage_repository
        self.test_repository = test_repository

    async def execute(self, passage_id: str, request: UpdatePassageRequest) -> Passage:
        """
        Update an existing passage with new data

        Args:
            passage_id: ID of the passage to update
            request: Update passage request with new data

        Returns:
            Updated passage entity

        Raises:
            PassageNotFoundError: If passage doesn't exist
            PassageInPublishedTestError: If passage is part of a published test
        """
        # Check if passage exists
        existing_passage = await self.passage_repository.get_by_id_with_questions(
            passage_id
        )
        if not existing_passage:
            raise PassageNotFoundError(passage_id)

        # Check if passage is in any published test
        is_in_published_test = await self.test_repository.is_passage_in_published_test(
            passage_id
        )
        if is_in_published_test:
            raise PassageInPublishedTestError(passage_id)

        # Build updated passage domain entity
        updated_passage = self._build_passage_entity(
            passage_id,
            request,
            existing_passage.created_by,
            existing_passage.created_at,
        )

        # Persist updates
        return await self.passage_repository.update_passage(updated_passage)

    def _build_passage_entity(
        self,
        passage_id: str,
        request: UpdatePassageRequest,
        created_by: str,
        created_at,
    ) -> Passage:
        """Build a complete Passage domain entity from the request"""

        # Calculate word count
        word_count = len(request.content.split()) if request.content else 0

        # Create passage aggregate root
        passage = Passage(
            id=passage_id,
            title=request.title,
            content=request.content,
            word_count=word_count,
            difficulty_level=request.difficulty_level,
            topic=request.topic,
            source=request.source,
            created_by=created_by,
            created_at=created_at,
            updated_at=TimeHelper.utc_now(),
        )

        # Create question groups
        for qg_dto in request.question_groups:
            options = []
            if qg_dto.options:
                options = [
                    Option(label=opt.label, text=opt.text) for opt in qg_dto.options
                ]

            # Create empty questions list - questions will be added later
            question_group = QuestionGroup(
                id=qg_dto.id,
                group_instructions=qg_dto.group_instructions,
                question_type=qg_dto.question_type,
                start_question_number=qg_dto.start_question_number,
                end_question_number=qg_dto.end_question_number,
                order_in_passage=qg_dto.order_in_passage,
                options=options,
                questions=[],
            )

            passage.add_question_group(question_group)

        # Create questions
        for q_dto in request.questions:
            options = None
            if q_dto.options:
                options = [
                    Option(label=opt.label, text=opt.text) for opt in q_dto.options
                ]

            # Create correct answer value object
            # Transform request format to domain model format
            correct_answer_data = q_dto.correct_answer
            if "acceptable_answers" in correct_answer_data and correct_answer_data["acceptable_answers"]:
                # Request format: {'answer': 'X', 'acceptable_answers': ['X', 'Y', 'Z']}
                # Transform to domain format: {'value': ['X', 'Y', 'Z']}
                correct_answer = CorrectAnswer(
                    value=correct_answer_data["acceptable_answers"]
                )
            elif "value" in correct_answer_data:
                # Already in correct format
                correct_answer = CorrectAnswer(**correct_answer_data)
            else:
                # Fallback: use 'answer' field as single value
                correct_answer = CorrectAnswer(
                    value=correct_answer_data.get("answer", "")
                )

            question = Question(
                question_group_id=q_dto.question_group_id,
                question_number=q_dto.question_number,
                question_type=q_dto.question_type,
                question_text=q_dto.question_text,
                options=options,
                correct_answer=correct_answer,
                explanation=q_dto.explanation,
                instructions=q_dto.instructions,
                points=q_dto.points,
                order_in_passage=q_dto.order_in_passage,
            )

            passage.add_question(question)

        # Validate the complete aggregate
        passage.validate_integrity()

        return passage
