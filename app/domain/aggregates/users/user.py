import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.common.utils.time_helper import TimeHelper


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    TEACHER = "TEACHER"
    STUDENT = "STUDENT"


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password_hash: str
    role: UserRole = Field(default=UserRole.STUDENT)
    full_name: str = Field(min_length=4, max_length=100)
    created_at: datetime = Field(default_factory=TimeHelper.utc_now)
    is_active: bool = True
