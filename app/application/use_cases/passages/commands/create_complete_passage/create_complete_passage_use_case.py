from app.application.use_cases.base.use_case import UseCase
from app.application.use_cases.passages.commands.create_complete_passage.create_complete_passage_dtos import (
    CompletePassageResponse,
    CreateCompletePassageRequest,
)
from app.domain.entities.passage import Passage
from app.domain.entities.question import Question, QuestionGroup
from app.domain.repositories.passage_repository import PassageRepositoryInterface
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option


class CreateCompletePassageUseCase(
    UseCase[CreateCompletePassageRequest, CompletePassageResponse]
):
    """Use case for creating a complete passage with questions and question groups"""

    def __init__(self, passage_repository: PassageRepositoryInterface):
        self.passage_repository = passage_repository

    async def execute(
        self, request: CreateCompletePassageRequest, user_id: str
    ) -> CompletePassageResponse:
        """
        Create a complete passage with questions and question groups

        Args:
            request: CreateCompletePassageRequest with passage and question data
            user_id: ID of the user creating the passage

        Returns:
            CompletePassageResponse with created passage data

        Raises:
            ValueError: If validation fails or business rules are violated
        """
        # Calculate word count
        word_count = len(request.content.split()) if request.content else 0

        # Create passage domain entity
        passage = Passage(
            title=request.title,
            content=request.content,
            word_count=word_count,
            difficulty_level=request.difficulty_level,
            topic=request.topic,
            source=request.source,
            created_by=user_id,
            question_groups=[],
            questions=[],
        )

        # Add question groups
        for qg_dto in request.question_groups:
            # Convert group options if present
            group_options = None
            if qg_dto.options:
                group_options = [
                    Option(label=opt.label, text=opt.text) for opt in qg_dto.options
                ]

            question_group = QuestionGroup(
                id=qg_dto.id,
                group_instructions=qg_dto.group_instructions,
                question_type=qg_dto.question_type,
                start_question_number=qg_dto.start_question_number,
                end_question_number=qg_dto.end_question_number,
                order_in_passage=qg_dto.order_in_passage,
                options=group_options,
            )
            passage.add_question_group(question_group)

        # Add questions
        for q_dto in request.questions:
            # Convert options if present
            options = None
            if q_dto.options:
                options = [
                    Option(label=opt.label, text=opt.text) for opt in q_dto.options
                ]

            # Create correct answer value object
            # Transform AI response format to domain model format
            correct_answer_data = q_dto.correct_answer
            if "acceptable_answers" in correct_answer_data:
                # AI response format: {'answer': 'X', 'acceptable_answers': ['X', 'Y', 'Z']}
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

        # Validate passage integrity (will raise ValueError if invalid)
        passage.validate_integrity()

        # Persist the complete passage
        created_passage = await self.passage_repository.create_complete_passage(passage)

        return CompletePassageResponse.from_entity(created_passage)
