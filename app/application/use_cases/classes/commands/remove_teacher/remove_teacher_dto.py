from pydantic import BaseModel


class RemoveTeacherRequest(BaseModel):
    class_id: str
    teacher_id: str


class RemoveTeacherResponse(BaseModel):
    class_id: str
    teacher_id: str
    teacher_removed: bool
