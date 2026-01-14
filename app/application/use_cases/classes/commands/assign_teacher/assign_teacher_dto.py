from pydantic import BaseModel


class AssignTeacherRequest(BaseModel):
    class_id: str
    teacher_id: str


class AssignTeacherResponse(BaseModel):
    class_id: str
    teacher_id: str
    teacher_assigned: bool
