"""Class repository interface"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.aggregates.class_.class_ import Class


class ClassRepositoryInterface(ABC):
    """
    Repository interface for Class aggregate

    Defines the contract for persisting and retrieving Class aggregates.
    """

    @abstractmethod
    async def create(self, class_entity: Class) -> Class:
        """
        Create a new class_

        Args:
            class_entity: The class_ to create

        Returns:
            The created class_
        """
        pass

    @abstractmethod
    async def get_by_id(self, class_id: str) -> Optional[Class]:
        """
        Get a class_ by ID

        Args:
            class_id: The class_ ID

        Returns:
            The class_ if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_all(self, teacher_id: Optional[str] = None) -> List[Class]:
        """
        Get all classes, optionally filtered by teacher

        Args:
            teacher_id: Optional teacher ID to filter by

        Returns:
            List of classes
        """
        pass

    @abstractmethod
    async def get_by_teacher(self, teacher_id: str) -> List[Class]:
        """
        Get all classes for a specific teacher

        Args:
            teacher_id: The teacher ID

        Returns:
            List of classes
        """
        pass

    @abstractmethod
    async def update(self, class_entity: Class) -> Class:
        """
        Update a class_

        Args:
            class_entity: The class_ to update

        Returns:
            The updated class_
        """
        pass

    @abstractmethod
    async def delete(self, class_id: str) -> bool:
        """
        Delete a class_

        Args:
            class_id: The class_ ID

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def is_student_enrolled_in_any_class(self, student_id: str) -> bool:
        """
        Check if a student is enrolled in any class_

        Args:
            student_id: The student ID

        Returns:
            True if enrolled in at least one class_, False otherwise
        """
        pass
