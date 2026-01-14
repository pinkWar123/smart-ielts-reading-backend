from typing import List

from pydantic import BaseModel

from app.application.services.common.user_dto import UserDto


class RemoveStudentRequest(BaseModel):
    class_id: str
    student_id: str


class RemoveStudentResponse(BaseModel):
    class_id: str
    student_id: str
    student_removed: bool
    students: List[UserDto]  # List of students after removal
