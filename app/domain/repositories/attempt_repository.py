"""Attempt repository interface"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.aggregates.attempt.attempt import Attempt


class AttemptRepositoryInterface(ABC):
    """
    Repository interface for Attempt aggregate

    Defines the contract for persisting and retrieving Attempt aggregates.
    """

    @abstractmethod
    async def create(self, attempt: Attempt) -> Attempt:
        """
        Create a new attempt

        Args:
            attempt: The attempt to create

        Returns:
            The created attempt
        """
        pass

    @abstractmethod
    async def get_by_id(self, attempt_id: str) -> Optional[Attempt]:
        """
        Get an attempt by ID

        Args:
            attempt_id: The attempt ID

        Returns:
            The attempt if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_student(self, student_id: str) -> List[Attempt]:
        """
        Get all attempts by a specific student

        Args:
            student_id: The student ID

        Returns:
            List of attempts
        """
        pass

    @abstractmethod
    async def get_by_test(self, test_id: str) -> List[Attempt]:
        """
        Get all attempts for a specific test

        Args:
            test_id: The test ID

        Returns:
            List of attempts
        """
        pass

    @abstractmethod
    async def get_by_session(self, session_id: str) -> List[Attempt]:
        """
        Get all attempts for a specific session

        Args:
            session_id: The session ID

        Returns:
            List of attempts
        """
        pass

    @abstractmethod
    async def get_by_student_and_test(
        self, student_id: str, test_id: str
    ) -> Optional[Attempt]:
        """
        Get a student's attempt for a specific test

        Args:
            student_id: The student ID
            test_id: The test ID

        Returns:
            The attempt if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_student_and_session(
        self, student_id: str, session_id: str
    ) -> Optional[Attempt]:
        """
        Get a student's attempt for a specific session

        Args:
            student_id: The student ID
            session_id: The session ID

        Returns:
            The attempt if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(self, attempt: Attempt) -> Attempt:
        """
        Update an attempt

        Args:
            attempt: The attempt to update

        Returns:
            The updated attempt
        """
        pass

    @abstractmethod
    async def delete(self, attempt_id: str) -> bool:
        """
        Delete an attempt

        Args:
            attempt_id: The attempt ID

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def get_in_progress_attempts_by_session(
        self, session_id: str
    ) -> List[Attempt]:
        """
        Get all in-progress attempts for a session

        Args:
            session_id: The session ID

        Returns:
            List of in-progress attempts
        """
        pass
