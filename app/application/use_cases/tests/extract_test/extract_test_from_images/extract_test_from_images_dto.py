from typing import List, Optional

from pydantic import BaseModel, Field

from app.domain.entities.question import QuestionType
from app.domain.entities.test import TestType


class ExtractedCorrectAnswer(BaseModel):
    """Correct answer structure"""

    answer: Optional[str | List[str]] = None
    acceptable_answers: List[str] = Field(default_factory=list)


class ExtractedOption(BaseModel):
    """Option for multiple choice or matching questions"""

    label: str  # e.g., "A", "B", "C" or "i", "ii", "iii"
    text: str


class ExtractedQuestion(BaseModel):
    """A single extracted question - matches QuestionDTO format"""

    question_number: int
    question_type: QuestionType
    question_text: str
    options: Optional[List[ExtractedOption]] = None
    correct_answer: ExtractedCorrectAnswer
    explanation: Optional[str] = None
    instructions: Optional[str] = None
    points: int = Field(default=1)
    order_in_passage: int
    question_group_id: Optional[str] = None


class ExtractedQuestionGroup(BaseModel):
    """A group of questions - matches QuestionGroupDTO format"""

    id: str
    group_instructions: str
    question_type: QuestionType
    start_question_number: int
    end_question_number: int
    order_in_passage: int


class ExtractedPassage(BaseModel):
    """Extracted passage - matches CreateCompletePassageRequest format"""

    title: str
    content: str
    difficulty_level: int = Field(ge=1, le=5, default=1)
    topic: str
    source: Optional[str] = None
    question_groups: List[ExtractedQuestionGroup] = Field(default_factory=list)
    questions: List[ExtractedQuestion]


class TestMetadata(BaseModel):
    """Metadata about the extracted test"""

    title: Optional[str] = None
    description: Optional[str] = None
    total_questions: int
    estimated_time_minutes: int = Field(default=60)
    test_type: TestType = Field(default=TestType.FULL_TEST)


class ExtractedTestResponse(BaseModel):
    """Complete extracted test response - ready to create passages and test"""

    passages: List[ExtractedPassage]
    test_metadata: TestMetadata
    extraction_notes: Optional[List[str]] = Field(default_factory=list)
    confidence_score: Optional[float] = None


class ImagesExtractRequest(BaseModel):
    """Request to extract test from multiple images"""

    images: List[bytes] = Field(..., description="List of image data in bytes")
    test_title: Optional[str] = None
    extraction_hints: Optional[str] = None  # User can provide hints about the content
