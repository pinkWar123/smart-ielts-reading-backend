from pydantic import BaseModel


class DeletePassageByIdRequest(BaseModel):
    test_id: str
    passage_id: str


class DeletePassageByIdResponse(BaseModel):
    passage_id: str
    passage_count: int  # number of passages in the test after deletion
    deleted: bool
