from pydantic import BaseModel


class RegenerateTokensRequest(BaseModel):
    refresh_token: str


class RegenerateTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: str
    username: str
    full_name: str
    role: str
    email: str
