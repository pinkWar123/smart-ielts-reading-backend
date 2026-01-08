from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.aggregates.passage import Passage, Question, QuestionGroup, QuestionType
from app.domain.entities.test import TestStatus, TestType
from app.domain.value_objects.question_value_objects import Option


class CorrectAnswerDTO(BaseModel):
    """Correct answer structure"""

    answer: Optional[str | List[str]] = None
    acceptable_answers: List[str] = Field(default_factory=list)

    @classmethod
    def convert_to_dto(cls, correct_answer) -> "CorrectAnswerDTO":
        """Convert domain CorrectAnswer to DTO"""
        # Domain CorrectAnswer has a 'value' field, DTO has an 'answer' field
        return cls(
            answer=correct_answer.value if hasattr(correct_answer, "value") else None,
            acceptable_answers=[],
        )


class OptionDTO(BaseModel):
    """Option for multiple choice or matching questions"""

    label: str  # e.g., "A", "B", "C" or "i", "ii", "iii"
    text: str

    @classmethod
    def convert_to_dto(cls, option: Option) -> "OptionDTO":
        return cls(label=option.label, text=option.text)


class QuestionDTO(BaseModel):
    """A single extracted question - matches QuestionDTO format"""

    question_number: int
    question_type: QuestionType
    question_text: str
    options: Optional[List[OptionDTO]] = None
    correct_answer: Optional[CorrectAnswerDTO] = None
    explanation: Optional[str] = None
    instructions: Optional[str] = None
    points: int = Field(default=1)
    order_in_passage: int
    question_group_id: Optional[str] = None

    @classmethod
    def convert_to_dto(cls, question: Question, view: "UserView") -> "QuestionDTO":
        return cls(
            question_number=question.question_number,
            question_type=question.question_type,
            question_text=question.question_text,
            options=(
                [OptionDTO.convert_to_dto(opt) for opt in question.options]
                if question.options
                else []
            ),
            correct_answer=(
                CorrectAnswerDTO.convert_to_dto(question.correct_answer)
                if question.correct_answer and view == UserView.ADMIN
                else None
            ),
            explanation=question.explanation,
            instructions=question.instructions,
            points=question.points,
            order_in_passage=question.order_in_passage,
            question_group_id=question.question_group_id,
        )


class QuestionGroupDTO(BaseModel):
    """A group of questions - matches QuestionGroupDTO format"""

    id: str
    group_instructions: str
    question_type: QuestionType
    start_question_number: int
    end_question_number: int
    order_in_passage: int
    options: Optional[List[OptionDTO]] = Field(
        None, description="Shared options for all questions in this group"
    )
    questions: Optional[List[QuestionDTO]] = Field(
        None, description="Questions in this group"
    )

    @classmethod
    def convert_to_dto(
        cls, question_group: QuestionGroup, view: "UserView"
    ) -> "QuestionGroupDTO":
        return cls(
            id=question_group.id,
            group_instructions=question_group.group_instructions,
            question_type=question_group.question_type,
            start_question_number=question_group.start_question_number,
            end_question_number=question_group.end_question_number,
            order_in_passage=question_group.order_in_passage,
            options=(
                [OptionDTO.convert_to_dto(opt) for opt in question_group.options]
                if question_group.options
                else []
            ),
            questions=(
                [
                    QuestionDTO.convert_to_dto(question, view)
                    for question in question_group.questions
                ]
                if question_group.questions
                else []
            ),
        )


class PassageDTO(BaseModel):
    """Extracted passage - matches CreateCompletePassageRequest format"""

    title: str
    content: str
    difficulty_level: int = Field(ge=1, le=5, default=1)
    topic: str
    source: Optional[str] = None
    question_groups: List[QuestionGroupDTO] = Field(default_factory=list)

    @classmethod
    def convert_to_dto(cls, passage: Passage, view: "UserView") -> "PassageDTO":
        return cls(
            title=passage.title,
            content=passage.content,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            question_groups=(
                [
                    QuestionGroupDTO.convert_to_dto(question_group, view)
                    for question_group in passage.question_groups
                ]
                if passage.question_groups
                else []
            ),
        )


class UserInfo(BaseModel):
    id: str
    name: str
    email: str


class TestMetadata(BaseModel):
    """Metadata about the extracted test"""

    title: Optional[str] = None
    description: Optional[str] = None
    total_questions: int
    estimated_time_minutes: int = Field(default=60)
    type: TestType = Field(default=TestType.FULL_TEST)
    status: TestStatus = Field(default=TestStatus.DRAFT)
    created_by: UserInfo
    created_at: str
    updated_at: Optional[str] = None


class UserView(Enum):
    ADMIN = "ADMIN"
    USER = "USER"
