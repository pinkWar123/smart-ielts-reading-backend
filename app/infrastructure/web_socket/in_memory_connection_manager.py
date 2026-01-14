import asyncio
import logging
from typing import Dict

from starlette.websockets import WebSocket

from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)

logger = logging.getLogger(__name__)


class InMemoryConnectionManagerService(ConnectionManagerServiceInterface):
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, session_id: str, user_id: str, websocket: WebSocket):
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = {}
            self.active_connections[session_id][user_id] = websocket
            logger.info(f"User {user_id} connected to session {session_id}")

    async def disconnect(self, session_id: str, user_id: str):
        async with self._lock:
            if session_id in self.active_connections:
                if user_id in self.active_connections[session_id]:
                    del self.active_connections[session_id][user_id]
                    logger.info(
                        f"User {user_id} disconnected from session {session_id}"
                    )

                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id not in self.active_connections:
            return

        disconnected = []
        for user_id, websocket in self.active_connections[session_id].items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                disconnected.append(user_id)
                logger.warning(f"Error sending message to user {user_id}: {e}")

        for user_id in disconnected:
            await self.disconnect(session_id, user_id)

    async def send_personal_message(self, session_id: str, user_id: str, message: dict):
        if session_id not in self.active_connections:
            return

        if user_id not in self.active_connections[session_id]:
            return

        try:
            await self.active_connections[session_id][user_id].send_json(message)
        except Exception as e:
            logger.warning(f"Error sending message to user {user_id}: {e}")
            await self.disconnect(session_id, user_id)

    async def get_connected_users(self, session_id: str) -> list[str]:
        if session_id not in self.active_connections:
            return []

        return list(self.active_connections[session_id].keys())

    def is_user_connected(self, session_id: str, user_id: str) -> bool:
        if session_id not in self.active_connections:
            return False

        return user_id in self.active_connections[session_id]
