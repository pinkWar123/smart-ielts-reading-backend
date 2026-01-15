from typing import List

from pydantic import BaseModel


class Teacher(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    classes_: List[str]  # name of classes that this teacher teaches


class Student(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    classes_: List[str]  # name of classes that this student is enrolled in
