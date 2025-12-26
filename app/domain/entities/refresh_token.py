import datetime

from pydantic import BaseModel


class RefreshToken(BaseModel):
    token: str
    user_id: str
    issued_at: datetime
    expires_at: datetime
    revoked: bool = False
