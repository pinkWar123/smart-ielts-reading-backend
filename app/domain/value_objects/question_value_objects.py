"""Value objects for Question domain"""
from typing import List, Union
from pydantic import BaseModel, Field


class Option(BaseModel):
    """Option for multiple choice or matching questions - Value Object"""
    label: str = Field(..., description="e.g., 'A', 'B', 'C' or 'i', 'ii', 'iii'")
    text: str = Field(..., min_length=1)

    class Config:
        frozen = True  # Immutable value object


class CorrectAnswer(BaseModel):
    """Correct answer(s) for a question - Value Object"""
    value: Union[str, List[str]] = Field(..., description="Single answer or list of answers")

    class Config:
        frozen = True  # Immutable value object

    def is_correct(self, student_answer: Union[str, List[str]]) -> bool:
        """Check if student answer matches correct answer"""
        if isinstance(self.value, list) and isinstance(student_answer, list):
            return sorted(self.value) == sorted(student_answer)
        return self.value == student_answer
