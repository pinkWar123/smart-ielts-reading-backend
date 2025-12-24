import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = ("ADMIN",)
    STUDENT = "STUDENT"


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(regex=r"^[^@]+@[^@]+\.[^@]+$")
    password_hash: str
    role: UserRole = Field(default=UserRole.STUDENT)
    full_name: str = Field(min_length=4, max_length=100)
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
