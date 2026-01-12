from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.aggregates.class_ import Class
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.infrastructure.persistence.models import ClassModel
from app.infrastructure.persistence.models.class_student_association import (
    ClassStudentAssociation,
)
from app.infrastructure.persistence.models.class_teacher_association import (
    ClassTeacherAssociation,
)


class SQLClassRepository(ClassRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, class_entity: Class) -> Class:
        """Create a new class with teacher and student associations"""
        # Create the class model
        class_model = ClassModel(
            id=class_entity.id,
            name=class_entity.name,
            description=class_entity.description,
            status=class_entity.status,
            created_at=class_entity.created_at,
            created_by=class_entity.created_by,
            updated_at=class_entity.updated_at,
        )
        self.session.add(class_model)

        # Create teacher associations
        for teacher_id in class_entity.teacher_ids:
            association = ClassTeacherAssociation(
                class_id=class_entity.id, teacher_id=teacher_id
            )
            self.session.add(association)

        # Create student associations
        for student_id in class_entity.student_ids:
            association = ClassStudentAssociation(
                class_id=class_entity.id, student_id=student_id
            )
            self.session.add(association)

        await self.session.flush()
        await self.session.refresh(
            class_model, ["teacher_associations", "student_associations"]
        )

        return class_model.to_domain()

    async def get_by_id(self, class_id: str) -> Optional[Class]:
        """Retrieve a class by ID with teacher and student associations"""
        stmt = (
            select(ClassModel)
            .where(ClassModel.id == class_id)
            .options(
                selectinload(ClassModel.teacher_associations),
                selectinload(ClassModel.student_associations),
            )
        )
        result = await self.session.execute(stmt)
        class_model = result.scalar_one_or_none()

        if class_model is None:
            return None

        return class_model.to_domain()

    async def get_all(self, teacher_id: Optional[str] = None) -> List[Class]:
        """Retrieve all classes, optionally filtered by teacher"""
        stmt = select(ClassModel).options(
            selectinload(ClassModel.teacher_associations),
            selectinload(ClassModel.student_associations),
        )

        if teacher_id:
            stmt = stmt.join(ClassTeacherAssociation).where(
                ClassTeacherAssociation.teacher_id == teacher_id
            )

        result = await self.session.execute(stmt)
        class_models = result.scalars().all()

        return [class_model.to_domain() for class_model in class_models]

    async def get_by_teacher(self, teacher_id: str) -> List[Class]:
        """Retrieve all classes where the user is a teacher"""
        stmt = (
            select(ClassModel)
            .join(ClassTeacherAssociation)
            .where(ClassTeacherAssociation.teacher_id == teacher_id)
            .options(
                selectinload(ClassModel.teacher_associations),
                selectinload(ClassModel.student_associations),
            )
        )
        result = await self.session.execute(stmt)
        class_models = result.scalars().all()

        return [class_model.to_domain() for class_model in class_models]

    async def update(self, class_entity: Class) -> Class:
        """Update a class and sync teacher and student associations"""
        # Get existing class model
        stmt = (
            select(ClassModel)
            .where(ClassModel.id == class_entity.id)
            .options(
                selectinload(ClassModel.teacher_associations),
                selectinload(ClassModel.student_associations),
            )
        )
        result = await self.session.execute(stmt)
        class_model = result.scalar_one_or_none()

        if class_model is None:
            raise ValueError(f"Class with id {class_entity.id} not found")

        # Update class attributes
        class_model.name = class_entity.name
        class_model.description = class_entity.description
        class_model.status = class_entity.status
        class_model.updated_at = class_entity.updated_at

        # Sync teacher associations
        existing_teacher_ids = {
            assoc.teacher_id for assoc in class_model.teacher_associations
        }
        new_teacher_ids = set(class_entity.teacher_ids)

        # Remove teachers no longer assigned
        teachers_to_remove = existing_teacher_ids - new_teacher_ids
        if teachers_to_remove:
            await self.session.execute(
                delete(ClassTeacherAssociation)
                .where(ClassTeacherAssociation.class_id == class_entity.id)
                .where(ClassTeacherAssociation.teacher_id.in_(teachers_to_remove))
            )

        # Add new teachers
        teachers_to_add = new_teacher_ids - existing_teacher_ids
        for teacher_id in teachers_to_add:
            association = ClassTeacherAssociation(
                class_id=class_entity.id, teacher_id=teacher_id
            )
            self.session.add(association)

        # Sync student associations
        existing_student_ids = {
            assoc.student_id for assoc in class_model.student_associations
        }
        new_student_ids = set(class_entity.student_ids)

        # Remove students no longer in the class
        students_to_remove = existing_student_ids - new_student_ids
        if students_to_remove:
            await self.session.execute(
                delete(ClassStudentAssociation)
                .where(ClassStudentAssociation.class_id == class_entity.id)
                .where(ClassStudentAssociation.student_id.in_(students_to_remove))
            )

        # Add new students
        students_to_add = new_student_ids - existing_student_ids
        for student_id in students_to_add:
            association = ClassStudentAssociation(
                class_id=class_entity.id, student_id=student_id
            )
            self.session.add(association)

        await self.session.flush()
        await self.session.refresh(
            class_model, ["teacher_associations", "student_associations"]
        )

        return class_model.to_domain()

    async def delete(self, class_id: str) -> bool:
        """Delete a class and its associations"""
        stmt = select(ClassModel).where(ClassModel.id == class_id)
        result = await self.session.execute(stmt)
        class_model = result.scalar_one_or_none()

        if class_model is None:
            return False

        await self.session.delete(class_model)
        await self.session.flush()

        return True

    async def is_class_name_already_used(self, class_name: str) -> bool:
        stmt = select(ClassModel.id).where(ClassModel.name == class_name)
        result = await self.session.execute(stmt)
        return result.scalar() is not None
