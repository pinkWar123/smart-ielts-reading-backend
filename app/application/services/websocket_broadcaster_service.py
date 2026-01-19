import logging
from typing import Optional

from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.services.query.users.user_query_service import UserQueryService
from app.domain.aggregates.users.user import UserRole
from app.domain.repositories.user_repository import UserRepositoryInterface

logger = logging.getLogger(__name__)


class WebSocketBroadcasterService:
    """
    Service for broadcasting WebSocket messages with role-based filtering.

    This service wraps the ConnectionManager and adds the ability to:
    - Filter broadcasts by user role (e.g., only to teachers)
    - Broadcast student activity to teachers
    - Handle broadcast failures gracefully without affecting main operations
    """

    def __init__(
        self,
        connection_manager: ConnectionManagerServiceInterface,
        user_repository: UserRepositoryInterface,
    ):
        self.connection_manager = connection_manager
        self.user_repository = user_repository

    async def broadcast_to_teachers(self, session_id: str, message: dict) -> None:
        """
        Broadcast message only to teachers in session.

        Args:
            session_id: The session ID
            message: The message to broadcast
        """
        try:
            # Get all connected users in the session
            connected_user_ids = await self.connection_manager.get_connected_users(
                session_id
            )

            if not connected_user_ids:
                logger.debug(f"No connected users in session {session_id}")
                return

            # Filter to only teachers
            teacher_ids = []
            for user_id in connected_user_ids:
                user = await self.user_repository.get_by_id(user_id)
                if user and user.role == UserRole.TEACHER:
                    teacher_ids.append(user_id)

            # Send message to each teacher
            for teacher_id in teacher_ids:
                await self.connection_manager.send_personal_message(
                    session_id=session_id,
                    user_id=teacher_id,
                    message=message,
                )

            logger.debug(
                f"Broadcasted message to {len(teacher_ids)} teachers in session {session_id}"
            )

        except Exception as e:
            # Log error but don't raise - broadcast failures should not affect main operations
            logger.error(
                f"Failed to broadcast to teachers in session {session_id}: {e}",
                exc_info=True,
            )

    async def broadcast_student_activity(
        self, session_id: str, student_id: str, message: dict
    ) -> None:
        """
        Broadcast student activity to teachers in the session.

        This is a convenience method that filters to teachers and broadcasts.
        Used for real-time monitoring of student activities like answers, progress, etc.

        Args:
            session_id: The session ID
            student_id: The student performing the activity
            message: The activity message to broadcast
        """
        await self.broadcast_to_teachers(session_id, message)

    async def broadcast_to_all(self, session_id: str, message: dict) -> None:
        """
        Broadcast message to all users in session (both users and teachers).

        Args:
            session_id: The session ID
            message: The message to broadcast
        """
        try:
            await self.connection_manager.broadcast_to_session(
                session_id=session_id,
                message=message,
            )
            logger.debug(f"Broadcasted message to all users in session {session_id}")
        except Exception as e:
            logger.error(
                f"Failed to broadcast to all in session {session_id}: {e}",
                exc_info=True,
            )
