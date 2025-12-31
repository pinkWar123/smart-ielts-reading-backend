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
    MATCHING_FEATURES = "matching_features"
    MATCHING_SENTENCE_ENDINGS = "matching_sentence_endings"
    SENTENCE_COMPLETION = "sentence_completion"
    SUMMARY_COMPLETION = "summary_completion"
    NOTE_COMPLETION = "note_completion"
    TABLE_COMPLETION = "table_completion"
    FLOW_CHART_COMPLETION = "flow_chart_completion"
    DIAGRAM_LABEL_COMPLETION = "diagram_label_completion"
    SHORT_ANSWER = "short_answer"


class QuestionGroupModel(BaseModel):
    """A group of questions with shared instructions (common in IELTS)"""
    __tablename__ = "question_groups"

    passage_id = Column(String, ForeignKey("passages.id"), nullable=False)
    group_instructions = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    start_question_number = Column(Integer, nullable=False)
    end_question_number = Column(Integer, nullable=False)
    order_in_passage = Column(Integer, nullable=False)

    # Relationships
    passage = relationship("PassageModel", back_populates="question_groups")
    questions = relationship("QuestionModel", back_populates="question_group", cascade="all, delete-orphan")


class QuestionModel(BaseModel):
    __tablename__ = "questions"

    passage_id = Column(String, ForeignKey("passages.id"), nullable=False)
    question_group_id = Column(String, ForeignKey("question_groups.id"), nullable=True)
    question_number = Column(Integer, nullable=False)
    question_type = Column(Enum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    options = Column(JSON)  # For multiple choice, matching, etc. Stores list of {label, text} objects
    correct_answer = Column(JSON, nullable=False)  # Can be single or multiple answers
    explanation = Column(Text)
    instructions = Column(Text)  # e.g., "Choose NO MORE THAN TWO WORDS" (individual instruction, if any)
    points = Column(Integer, default=1)
    order_in_passage = Column(Integer, nullable=False)

    # Relationships
    passage = relationship("PassageModel", back_populates="questions")
    question_group = relationship("QuestionGroupModel", back_populates="questions")
