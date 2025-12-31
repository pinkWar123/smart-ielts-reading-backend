
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ExtractedQuestionType(str, Enum):
    """IELTS Reading question types"""
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TRUE_FALSE_NOTGIVEN = "TRUE_FALSE_NOTGIVEN"
    YES_NO_NOTGIVEN = "YES_NO_NOTGIVEN"
    MATCHING_HEADINGS = "MATCHING_HEADINGS"
    MATCHING_INFORMATION = "MATCHING_INFORMATION"
    MATCHING_FEATURES = "MATCHING_FEATURES"
    MATCHING_SENTENCE_ENDINGS = "MATCHING_SENTENCE_ENDINGS"
    SENTENCE_COMPLETION = "SENTENCE_COMPLETION"
    SUMMARY_COMPLETION = "SUMMARY_COMPLETION"
    NOTE_COMPLETION = "NOTE_COMPLETION"
    TABLE_COMPLETION = "TABLE_COMPLETION"
    FLOW_CHART_COMPLETION = "FLOW_CHART_COMPLETION"
    DIAGRAM_LABEL_COMPLETION = "DIAGRAM_LABEL_COMPLETION"
    SHORT_ANSWER = "SHORT_ANSWER"


class ExtractedOption(BaseModel):
    """Option for multiple choice or matching questions"""
    label: str  # e.g., "A", "B", "C" or "i", "ii", "iii"
    text: str


class ExtractedQuestion(BaseModel):
    """A single extracted question from the image"""
    question_number: int
    question_type: ExtractedQuestionType
    question_text: str
    options: Optional[List[ExtractedOption]] = None
    correct_answer: Optional[Union[str, List[str]]] = None  # May be null if answer not in images
    explanation: Optional[str] = None
    instructions: Optional[str] = None  # e.g., "Choose NO MORE THAN TWO WORDS"


class ExtractedQuestionGroup(BaseModel):
    """A group of questions with shared instructions (common in IELTS)"""
    group_instructions: str  # e.g., "Questions 1-5: Do the following statements agree with..."
    question_type: ExtractedQuestionType
    questions: List[ExtractedQuestion]
    start_question_number: int
    end_question_number: int


class ExtractedPassage(BaseModel):
    """Extracted passage/reading text"""
    title: Optional[str] = None
    content: str
    paragraphs: Optional[List[str]] = None  # For paragraph-labeled content (A, B, C...)
    word_count: Optional[int] = None
    source_image_index: int  # Which image this came from?


class ExtractedTestSection(BaseModel):
    """A section of the test (one passage and its questions)"""
    passage: ExtractedPassage
    question_groups: List[ExtractedQuestionGroup]
    total_questions: int


class ExtractedTestResponse(BaseModel):
    """Complete extracted test ready for frontend preview"""
    title: Optional[str] = None
    description: Optional[str] = None
    sections: List[ExtractedTestSection]
    total_questions: int
    estimated_time_minutes: int = Field(default=60)
    extraction_notes: Optional[List[str]] = None  # Any issues or notes from extraction
    confidence_score: Optional[float] = None  # Overall extraction confidence


class ImagesExtractRequest(BaseModel):
    """Request to extract test from multiple images"""
    images: List[bytes] = Field(..., description="List of image data in bytes")
    test_title: Optional[str] = None
    extraction_hints: Optional[str] = None  # User can provide hints about the content