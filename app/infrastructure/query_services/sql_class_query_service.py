import math
from typing import List, Optional

from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.common.user_dto import UserDto
from app.application.services.query.classes.class_query_model import (
    ClassDetailQueryModel,
    ClassSortField,
    ListClassesQueryModel,
    ListClassStudentsQueryModel,
)
from app.application.services.query.classes.class_query_service import ClassQueryService
from app.common.pagination import PaginatedResponse, PaginationMeta, SortOrder
from app.infrastructure.persistence.models import (
    ClassModel,
    ClassStudentAssociation,
    UserModel,
)
from app.infrastructure.persistence.models.class_teacher_association import (
    ClassTeacherAssociation,
)


class SqlClassQueryService(ClassQueryService):

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_class_by_id(self, class_id: str) -> Optional[ClassDetailQueryModel]:
        stmt = (
            select(
                ClassModel.id,
                ClassModel.name,
                ClassModel.description,
                ClassModel.status,
                ClassModel.created_at,
                UserModel,
            )
            .select_from(ClassModel)
            .outerjoin(ClassStudentAssociation)
            .outerjoin(UserModel, UserModel.id == ClassStudentAssociation.student_id)
            .where(ClassModel.id == class_id)
            .where(ClassModel.is_active == True)
        )

        result = await self.session.execute(stmt)
        rows = result.fetchall()

        if not rows:
            return None
        first_row = rows[0]
        students: List[UserDto] = []

        for row in rows:
            user_model = row[5]
            if user_model is not None:
                dto = UserDto(
                    id=user_model.id,
                    username=user_model.username,
                    email=user_model.email,
                    full_name=user_model.full_name,
                    role=user_model.role.value,
                )
                students.append(dto)

        teacher_stmt = (
            select(UserModel)
            .select_from(ClassTeacherAssociation)
            .join(UserModel, UserModel.id == ClassTeacherAssociation.teacher_id)
            .where(ClassTeacherAssociation.class_id == class_id)
        )

        teacher_result = await self.session.execute(teacher_stmt)
        teacher_rows = teacher_result.fetchall()
        teachers = (
            [
                UserDto(
                    id=row[0].id,
                    username=row[0].username,
                    email=row[0].email,
                    full_name=row[0].full_name,
                    role=row[0].role.value,
                )
                for row in teacher_rows
            ]
            if teacher_rows
            else []
        )

        creator_stmt = (
            select(UserModel)
            .select_from(ClassModel)
            .join(UserModel, UserModel.id == ClassModel.created_by)
            .where(ClassModel.id == class_id)
            .where(ClassModel.is_active == True)
        )

        creator_result = await self.session.execute(creator_stmt)
        creator_row = creator_result.scalar_one_or_none()

        if creator_row is None:
            creator_dto = None
        else:
            creator = creator_row.to_domain()
            creator_dto = UserDto(
                id=creator.id,
                username=creator.username,
                email=creator.email,
                full_name=creator.full_name,
                role=creator.role.value,
            )

        return ClassDetailQueryModel(
            id=first_row.id,
            name=first_row.name,
            description=first_row.description,
            status=first_row.status,
            created_at=first_row.created_at,
            created_by=creator_dto,
            students=students,
            teachers=teachers,
        )

    async def list_classes(
        self,
        page: int,
        page_size: int,
        sort_by: Optional[ClassSortField],
        sort_order: Optional[SortOrder],
        teacher_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> PaginatedResponse[ListClassesQueryModel]:
        """
        List classes with pagination, sorting, and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            teacher_id: Filter by teacher ID (classes taught by this teacher)
            name: Filter by class name (case-insensitive partial match)

        Optimizations:
        1. Only fetch users for classes in current page
        2. Proper column mapping for sorting
        3. Correct pagination calculations
        4. Efficient filtering with proper joins
        """
        # Map sort field enum to actual column
        sort_column_map = {
            ClassSortField.NAME: ClassModel.name,
            ClassSortField.CREATED_AT: ClassModel.created_at,
            ClassSortField.CREATED_BY: UserModel.username,  # Sort by creator's username
            ClassSortField.STATUS: ClassModel.status,
        }

        # Build base query with joins
        base_query = (
            select(ClassModel)
            .select_from(ClassModel)
            .join(UserModel, UserModel.id == ClassModel.created_by)
        )

        # Apply teacher filter if provided
        if teacher_id:
            base_query = base_query.join(
                ClassTeacherAssociation,
                ClassTeacherAssociation.class_id == ClassModel.id,
            ).where(ClassTeacherAssociation.teacher_id == teacher_id)

        # Apply name filter if provided (case-insensitive partial match)
        if name:
            base_query = base_query.where(ClassModel.name.ilike(f"%{name}%"))

        # Get total count with filters applied
        count_stmt = base_query.with_only_columns(func.count()).order_by(None)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        # Build main query with proper sorting using the filtered base query
        sort_column = sort_column_map.get(sort_by, ClassModel.created_at)
        order_clause = (
            desc(sort_column) if sort_order == SortOrder.DESC else asc(sort_column)
        )

        # Reconstruct query to select specific columns (reuse filter logic)
        main_stmt = (
            base_query.with_only_columns(
                ClassModel.id,
                ClassModel.name,
                ClassModel.description,
                ClassModel.status,
                ClassModel.created_at,
                UserModel,
            )
            .order_by(order_clause)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.session.execute(main_stmt)
        rows = result.fetchall()

        # If no results, return empty response
        if not rows:
            return PaginatedResponse(
                meta=PaginationMeta(
                    total_items=0,
                    current_page=page,
                    page_size=page_size,
                    has_next=False,
                    has_previous=page > 1,
                    total_pages=0,
                ),
                data=[],
            )

        # Extract class IDs from current page only
        class_ids = [row[0] for row in rows]

        # Fetch users ONLY for classes in current page (performance optimization)
        student_stmt = (
            select(ClassStudentAssociation.class_id, UserModel)
            .select_from(ClassStudentAssociation)
            .join(UserModel, UserModel.id == ClassStudentAssociation.student_id)
            .where(ClassStudentAssociation.class_id.in_(class_ids))
        )

        student_result = await self.session.execute(student_stmt)
        student_rows = student_result.fetchall()

        # Build class dictionary
        class_dict = {}
        for class_id, name, description, status, created_at, user_model in rows:
            class_dict[class_id] = {
                "id": class_id,
                "name": name,
                "description": description,
                "status": status,
                "created_at": created_at,
                "created_by": user_model.to_domain(),
                "users": [],
            }

        # Add users to their respective classes (now safe from KeyError)
        for class_id, user_model in student_rows:
            if user_model and class_id in class_dict:  # Null safety check
                query_model = ListClassStudentsQueryModel(
                    id=user_model.id,
                    username=user_model.username,
                    email=user_model.email,
                )
                class_dict[class_id]["users"].append(query_model)

        # Calculate pagination metadata correctly
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        has_next = page < total_pages

        return PaginatedResponse(
            meta=PaginationMeta(
                total_items=total_count,
                current_page=page,
                page_size=page_size,
                has_next=has_next,
                has_previous=page > 1,
                total_pages=total_pages,
            ),
            data=list(class_dict.values()),
        )
