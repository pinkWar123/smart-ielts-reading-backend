from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.query.users.user_query_model import Student, Teacher
from app.application.services.query.users.user_query_service import UserQueryService
from app.domain.aggregates.users.user import UserRole
from app.infrastructure.persistence.models import (
    ClassModel,
    ClassStudentAssociation,
    ClassTeacherAssociation,
    UserModel,
)


class SQLUserQueryService(UserQueryService):
    async def get_teachers_by_ids(self, teacher_ids: List[str]) -> List[Teacher]:
        stmt = (
            select(
                UserModel.id,
                UserModel.username,
                UserModel.full_name,
                UserModel.email,
                ClassModel.name,
            )
            .select_from(UserModel)
            .outerjoin(UserModel.teaching_associations)
            .outerjoin(ClassModel, ClassModel.id == ClassTeacherAssociation.class_id)
            .where(UserModel.id.in_(teacher_ids))
            .where(UserModel.role.in_([UserRole.TEACHER, UserRole.ADMIN]))
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        teacher_dict = {}
        for teacher_id, username, full_name, email, class_name in rows:
            if teacher_id not in teacher_dict:
                teacher_dict[teacher_id] = {
                    "id": teacher_id,
                    "username": username,
                    "full_name": full_name,
                    "email": email,
                    "classes_": [],
                }
            if class_name:
                teacher_dict[teacher_id]["classes_"].append(class_name)
        teachers = []
        print(teacher_dict)
        for teacher_id, teacher_data in teacher_dict.items():
            teachers.append(Teacher(**teacher_data))

        return teachers

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_teacher_by_id(self, teacher_id: str) -> Optional[Teacher]:
        """
        Get teacher by ID with their taught classes.

        Args:
            teacher_id: The teacher's user ID (string UUID)

        Returns:
            Teacher object with classes, or None if not found or user is not a teacher
        """
        # Single efficient query with LEFT JOIN to get user and all their classes
        stmt = (
            select(
                UserModel.id,
                UserModel.username,
                UserModel.full_name,
                UserModel.email,
                ClassModel.name,
            )
            .select_from(UserModel)
            .outerjoin(UserModel.teaching_associations)
            .outerjoin(ClassModel, ClassModel.id == ClassTeacherAssociation.class_id)
            .where(UserModel.id == teacher_id)
            .where(UserModel.role.in_([UserRole.TEACHER, UserRole.ADMIN]))
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return None

        first_row = rows[0]

        # Collect all class names (filter out None for teachers with no classes)
        class_names = [row.name for row in rows if row.name is not None]

        return Teacher(
            id=first_row.id,
            username=first_row.username,
            full_name=first_row.full_name,
            email=first_row.email,
            classes_=class_names,
        )

    async def get_student_by_id(self, student_id: int) -> Optional[Student]:
        stmt = (
            select(
                UserModel.id,
                UserModel.username,
                UserModel.full_name,
                UserModel.email,
                ClassModel.name,
            )
            .select_from(UserModel)
            .outerjoin(UserModel.class_associations)
            .outerjoin(ClassModel, ClassModel.id == ClassStudentAssociation.class_id)
            .where(UserModel.id == student_id)
            .where(UserModel.role == UserRole.STUDENT)
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        first_row = rows[0]
        class_names = [row.name for row in rows if row.name is not None]

        return Student(
            id=first_row.id,
            username=first_row.username,
            full_name=first_row.full_name,
            email=first_row.email,
            classes_=class_names,
        )

    async def get_students_by_ids(self, student_ids: List[str]) -> List[Student]:
        stmt = (
            select(
                UserModel.id,
                UserModel.username,
                UserModel.full_name,
                UserModel.email,
                ClassModel.name,
            )
            .select_from(UserModel)
            .outerjoin(UserModel.class_associations)
            .outerjoin(ClassModel, ClassModel.id == ClassStudentAssociation.class_id)
            .where(UserModel.id.in_(student_ids))
            .where(UserModel.role == UserRole.STUDENT)
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        student_dict = {}
        for student_id, username, full_name, email, class_name in rows:
            if student_id not in student_dict:
                student_dict[student_id] = {
                    "id": student_id,
                    "username": username,
                    "full_name": full_name,
                    "email": email,
                    "classes_": [],
                }
            if class_name:
                student_dict[student_id]["classes_"].append(class_name)

        students = []
        for student_id, student_data in student_dict.items():
            students.append(Student(**student_data))

        return students
