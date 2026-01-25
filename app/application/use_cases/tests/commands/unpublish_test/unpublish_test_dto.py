from pydantic import BaseModel


class UnpublishTestCommand(BaseModel):
    id: str


class UnpublishTestResponse(BaseModel):
    success: bool
    message: str
