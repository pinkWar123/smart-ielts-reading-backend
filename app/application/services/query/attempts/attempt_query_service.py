from abc import ABC, abstractmethod

from app.application.services.query.attempts.attempt_query_model import AttemptDetail


class AttemptQueryService(ABC):
    @abstractmethod
    async def get_attempt_by_id(self, attempt_id: str) -> AttemptDetail | None:
        pass
