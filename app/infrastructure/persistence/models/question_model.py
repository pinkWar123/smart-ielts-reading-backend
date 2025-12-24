import enum

from sqlalchemy import JSON, Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.infrastructure.persistence.models.base import BaseModel


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE_NOT_GIVEN = "true_false_not_given"
    YES_NO_NOT_GIVEN = "yes_no_not_given"
    MATCHING_HEADINGS = "matching_headings"
    MATCHING_INFORMATION = "matching_information"
    SENTENCE_COMPLETION = "sentence_completion"
    SUMMARY_COMPLETION = "summary_completion"
    SHORT_ANSWER = "short_answer"


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    passage_id = Column(String, ForeignKey("passages.id"), nullable=False)
    question_number = Column(Integer, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON)  # For multiple choice, matching, etc.
    correct_answer = Column(JSON, nullable=False)  # Can be single or multiple answers
    explanation = Column(Text)
    points = Column(Integer, default=1)
    order_in_passage = Column(Integer, nullable=False)

    # Relationships
    passage = relationship("PassageModel", back_populates="questions")
