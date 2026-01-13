from pydantic import BaseModel


class UserDto(BaseModel):
    id: str
    username: str
    email: str
    role: str
    full_name: str
