from typing import List, Optional

from pydantic import BaseModel

from app.domain.aggregates.users.user import UserRole


class ListUserQuery(BaseModel):
    search: str
    limit: int
    role: Optional[UserRole]


class UserDTO(BaseModel):
    id: str
    username: str
    full_name: str
    email: str
    role: UserRole


class ListUsersResponse(BaseModel):
    users: List[UserDTO]
