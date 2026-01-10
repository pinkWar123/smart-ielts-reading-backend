from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.domain.aggregates.users.user import UserRole


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=20)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole = Field(default=UserRole.STUDENT)
    email: EmailStr


class RegisterResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    username: str
    role: str
    email: str
    full_name: str
