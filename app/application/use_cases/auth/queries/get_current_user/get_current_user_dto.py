from pydantic import BaseModel


class GetCurrentUserQuery(BaseModel):
    access_token: str


class GetCurrentUserResponse(BaseModel):
    username: str
    role: str
    user_id: str
    email: str
    full_name: str
    exp: int
