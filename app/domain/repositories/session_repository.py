"""Session repository interface"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.common.pagination import SortableParams
from app.domain.aggregates.session import Session


class SessionRepositoryInterface(ABC):
    """
    Repository interface for Session aggregate

    Defines the contract for persisting and retrieving Session aggregates.
    """

    @abstractmethod
    async def create(self, session: Session) -> Session:
        """
        Create a new session

        Args:
            session: The session to create

        Returns:
            The created session
        """
        pass

    @abstractmethod
    async def get_by_id(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID

        Args:
            session_id: The session ID

        Returns:
            The session if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_class(
        self, class_id: str, params: SortableParams
    ) -> List[Session]:
        """
        Get all sessions for a specific class_

        Args:
            class_id: The class_ ID

        Returns:
            List of sessions
        """
        pass

    @abstractmethod
    async def get_by_student(
        self, student_id: str, params: SortableParams
    ) -> List[Session]:
        """
        Get all sessions where a student is a participant

        Args:
            student_id: The student ID

        Returns:
            List of sessions
        """
        pass

    @abstractmethod
    async def get_by_teacher(
        self, teacher_id: str, params: SortableParams
    ) -> List[Session]:
        """
        Get all sessions created by a specific teacher

        Args:
            teacher_id: The teacher ID

        Returns:
            List of sessions
        """
        pass

    @abstractmethod
    async def update(self, session: Session) -> Session:
        """
        Update a session

        Args:
            session: The session to update

        Returns:
            The updated session
        """
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: The session ID

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def get_active_sessions(self, params: SortableParams) -> List[Session]:
        """
        Get all active sessions (WAITING_FOR_STUDENTS or IN_PROGRESS)

        Returns:
            List of active sessions
        """
        pass

    @abstractmethod
    async def count_by_student(self, student_id: str) -> int:
        """
        Count all sessions where a student is a participant

        Args:
            student_id: The student ID

        Returns:
            Count of sessions
        """
        pass

    @abstractmethod
    async def count_by_teacher(self, teacher_id: str) -> int:
        """
        Count all sessions created by a specific teacher

        Args:
            teacher_id: The teacher ID

        Returns:
            Count of sessions
        """
        pass

    @abstractmethod
    async def count_by_class(self, class_id: str) -> int:
        """
        Count all sessions for a specific class

        Args:
            class_id: The class ID

        Returns:
            Count of sessions
        """
        pass

    @abstractmethod
    async def count_active_sessions(self) -> int:
        """
        Count all active sessions (WAITING_FOR_STUDENTS or IN_PROGRESS)

        Returns:
            Count of active sessions
        """
        pass
