from pydantic import BaseModel

from app.application.use_cases.attempts.queries.get_by_id.get_by_id_dto import (
    GetAttemptByIdResponse,
)


class GetMyAttemptQuery(BaseModel):
    session_id: str


class GetMyAttemptResponse(GetAttemptByIdResponse):
    pass
