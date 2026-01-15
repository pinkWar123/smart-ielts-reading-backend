from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.domain.aggregates.passage import Passage, Question, QuestionGroup, QuestionType
from app.domain.value_objects.question_value_objects import CorrectAnswer, Option
from app.infrastructure.persistence.models.base import BaseModel


class PassageModel(BaseModel):
    __tablename__ = "passages"

    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, default=0)
    difficulty_level = Column(Integer, default=1)  # 1-5 scale
    topic = Column(String(100), nullable=False)
    source = Column(String(255))
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_deleted = Column(Boolean, default=False)

    # Relationships
    creator = relationship("UserModel", back_populates="created_passages")
    questions = relationship(
        "QuestionModel", back_populates="passage", cascade="all, delete-orphan"
    )
    question_groups = relationship(
        "QuestionGroupModel", back_populates="passage", cascade="all, delete-orphan"
    )

    # Many-to-many relationship with tests will be handled through TestPassage association table

    def to_domain(self) -> Passage:
        """Convert PassageModel to Passage domain entity with questions and question groups"""

        # Convert question groups
        question_groups = []
        questions = []
        if self.question_groups:
            for qg_model in self.question_groups:
                group_options = None
                if qg_model.options:
                    group_options = [Option(**opt) for opt in qg_model.options]
                question_group = QuestionGroup(
                    id=qg_model.id,
                    group_instructions=qg_model.group_instructions,
                    question_type=QuestionType(qg_model.question_type),
                    start_question_number=qg_model.start_question_number,
                    end_question_number=qg_model.end_question_number,
                    order_in_passage=qg_model.order_in_passage,
                    options=group_options or [],
                    questions=[],
                )

                if qg_model.questions:
                    current_questions = []
                    for q_model in qg_model.questions:
                        q_options = None
                        if q_model.options:
                            q_options = [Option(**opt) for opt in q_model.options]

                        question = Question(
                            id=q_model.id,
                            question_group_id=q_model.question_group_id,
                            question_number=q_model.question_number,
                            question_type=QuestionType(q_model.question_type),
                            question_text=q_model.question_text,
                            options=q_options,
                            correct_answer=CorrectAnswer(**q_model.correct_answer),
                            explanation=q_model.explanation,
                            instructions=q_model.instructions,
                            points=q_model.points,
                            order_in_passage=q_model.order_in_passage,
                        )

                        questions.append(question)
                        question_group.add_question(question)
                question_groups.append(question_group)

        return Passage(
            id=self.id,
            title=self.title,
            content=self.content,
            word_count=self.word_count or 0,
            difficulty_level=self.difficulty_level or 1,
            topic=self.topic or "General",
            source=self.source,
            created_by=self.created_by,
            created_at=self.created_at,
            updated_at=self.updated_at,
            is_active=self.is_active,
            question_groups=question_groups,
            questions=questions,
        )
