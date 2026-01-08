from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.entities.passage import Passage
from app.domain.entities.question import QuestionType


class QuestionOptionDTO(BaseModel):
    """DTO for question options (for multiple choice, matching, etc.)"""

    label: str = Field(description="Option label (A, B, C, etc.)")
    text: str = Field(description="Option text content")


class QuestionDTO(BaseModel):
    """DTO for creating a question"""

    question_number: int = Field(ge=1, description="Question number in the passage")
    question_type: QuestionType
    question_text: str = Field(min_length=1)
    options: Optional[List[QuestionOptionDTO]] = None
    correct_answer: dict = Field(
        description="Correct answer(s) - structure depends on question type"
    )
    explanation: Optional[str] = None
    instructions: Optional[str] = Field(
        None, description="Individual question instructions (if not in a group)"
    )
    points: int = Field(default=1, ge=1)
    order_in_passage: int = Field(ge=1)
    question_group_id: Optional[str] = Field(
        None, description="ID of the question group this belongs to"
    )


class QuestionGroupDTO(BaseModel):
    """DTO for creating a question group"""

    id: str = Field(description="Unique ID for the group (to link questions)")
    group_instructions: str = Field(min_length=1)
    question_type: QuestionType
    start_question_number: int = Field(ge=1)
    end_question_number: int = Field(ge=1)
    order_in_passage: int = Field(ge=1)
    options: Optional[List[QuestionOptionDTO]] = Field(
        None, description="Shared options for all questions in this group"
    )


class CreateCompletePassageRequest(BaseModel):
    """Request to create a complete passage with questions and groups"""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    difficulty_level: int = Field(ge=1, le=5, default=1)
    topic: str = Field(min_length=1, max_length=255)
    source: Optional[str] = None
    question_groups: List[QuestionGroupDTO] = Field(default_factory=list)
    questions: List[QuestionDTO] = Field(
        min_length=1, description="At least one question is required"
    )


class QuestionResponseDTO(BaseModel):
    """Response DTO for a question"""

    id: str
    question_number: int
    question_type: QuestionType
    question_text: str
    options: Optional[List[QuestionOptionDTO]]
    correct_answer: dict
    explanation: Optional[str]
    instructions: Optional[str]
    points: int
    order_in_passage: int
    question_group_id: Optional[str]


class QuestionGroupResponseDTO(BaseModel):
    """Response DTO for a question group"""

    id: str
    group_instructions: str
    question_type: QuestionType
    start_question_number: int
    end_question_number: int
    order_in_passage: int
    options: Optional[List[QuestionOptionDTO]]


class CompletePassageResponse(BaseModel):
    """Response containing complete passage data with questions"""

    id: str
    title: str
    content: str
    word_count: int
    difficulty_level: int
    topic: str
    source: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    question_groups: List[QuestionGroupResponseDTO]
    questions: List[QuestionResponseDTO]

    @classmethod
    def from_entity(cls, passage: Passage) -> "CompletePassageResponse":
        """Create a CompletePassageResponse from a Passage domain entity"""
        question_groups = [
            QuestionGroupResponseDTO(
                id=qg.id,
                group_instructions=qg.group_instructions,
                question_type=qg.question_type,
                start_question_number=qg.start_question_number,
                end_question_number=qg.end_question_number,
                order_in_passage=qg.order_in_passage,
                options=(
                    [
                        QuestionOptionDTO(label=opt.label, text=opt.text)
                        for opt in qg.options
                    ]
                    if qg.options
                    else None
                ),
            )
            for qg in passage.question_groups
        ]

        questions = [
            QuestionResponseDTO(
                id=q.id,
                question_number=q.question_number,
                question_type=q.question_type,
                question_text=q.question_text,
                options=(
                    [
                        QuestionOptionDTO(label=opt.label, text=opt.text)
                        for opt in q.options
                    ]
                    if q.options
                    else None
                ),
                correct_answer=q.correct_answer.model_dump(),
                explanation=q.explanation,
                instructions=q.instructions,
                points=q.points,
                order_in_passage=q.order_in_passage,
                question_group_id=q.question_group_id,
            )
            for q in passage.questions
        ]

        return cls(
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
            question_groups=question_groups,
            questions=questions,
        )
