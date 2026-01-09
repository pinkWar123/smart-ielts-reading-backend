from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.domain.aggregates.passage import QuestionType


class QuestionOptionDTO(BaseModel):
    """DTO for question options (for multiple choice, matching, etc.)"""

    label: str = Field(description="Option label (A, B, C, etc.)")
    text: str = Field(description="Option text content")


class UpdateQuestionDTO(BaseModel):
    """DTO for updating a question"""

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


class UpdateQuestionGroupDTO(BaseModel):
    """DTO for updating a question group"""

    id: str = Field(description="Unique ID for the group (to link questions)")
    group_instructions: str = Field(min_length=1)
    question_type: QuestionType
    start_question_number: int = Field(ge=1)
    end_question_number: int = Field(ge=1)
    order_in_passage: int = Field(ge=1)
    options: Optional[List[QuestionOptionDTO]] = Field(
        None, description="Shared options for all questions in this group"
    )


class UpdatePassageRequest(BaseModel):
    """Request to update a passage with questions and groups"""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    difficulty_level: int = Field(ge=1, le=5)
    topic: str = Field(min_length=1, max_length=255)
    source: Optional[str] = None
    question_groups: List[UpdateQuestionGroupDTO] = Field(default_factory=list)
    questions: List[UpdateQuestionDTO] = Field(
        min_length=13, max_length=14, description="Passage must have 13-14 questions"
    )

    @field_validator("questions")
    @classmethod
    def validate_question_count(cls, v):
        """Validate that passage has exactly 13-14 questions"""
        if not (13 <= len(v) <= 14):
            raise ValueError("Passage must have exactly 13-14 questions")
        return v
