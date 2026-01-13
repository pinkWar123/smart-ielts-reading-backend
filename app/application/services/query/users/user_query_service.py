from abc import ABC, abstractmethod
from typing import List, Optional

from app.application.services.query.users.user_query_model import Student, Teacher


class UserQueryService(ABC):
    @abstractmethod
    async def get_teacher_by_id(self, teacher_id: int) -> Optional[Teacher]:
        pass

    @abstractmethod
    async def get_teachers_by_ids(self, teacher_ids: List[str]) -> List[Teacher]:
        pass

    @abstractmethod
    async def get_student_by_id(self, student_id: int) -> Optional[Student]:
        pass

    @abstractmethod
    async def get_students_by_ids(self, student_ids: List[str]) -> List[Student]:
        pass
