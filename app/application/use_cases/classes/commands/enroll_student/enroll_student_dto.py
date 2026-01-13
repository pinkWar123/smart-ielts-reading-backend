from datetime import datetime

from pydantic import BaseModel


class EnrollStudentRequest(BaseModel):
    class_id: str
    student_id: str


class EnrollStudentResponse(BaseModel):
    student_id: str
    enrollment_date: datetime
