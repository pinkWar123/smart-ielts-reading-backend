from abc import ABC, abstractmethod

from starlette.websockets import WebSocket


class ConnectionManagerServiceInterface(ABC):

    @abstractmethod
    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        pass

    @abstractmethod
    async def disconnect(self, session_id: str, user_id: str):
        pass

    @abstractmethod
    async def broadcast_to_session(self, session_id: str, message: dict):
        pass

    @abstractmethod
    async def send_personal_message(self, session_id: str, user_id: str, message: dict):
        pass

    @abstractmethod
    async def get_connected_users(self, session_id: str) -> list[str]:
        pass

    @abstractmethod
    def is_user_connected(self, session_id: str, user_id: str) -> bool:
        pass
