from abc import ABC, abstractmethod

from app.application.services.query.passages.passages_query_model import PassageDetail


class PassagesQueryService(ABC):
    @abstractmethod
    async def get_passage_detail_by_id(self, passage_id: str) -> PassageDetail:
        pass
