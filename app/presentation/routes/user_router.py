from fastapi import APIRouter
from fastapi.params import Depends, Query

from app.application.users.students.queries.list_users.list_users_dto import (
    ListUserQuery,
)
from app.common.dependencies import UserUseCases, get_user_use_cases
from app.domain.aggregates.users.user import UserRole

router = APIRouter()


@router.get(
    "",
    summary="List Users",
)
async def list_users(
    role: UserRole = Query(default=None, description="User role needs to query"),
    limit: int = Query(
        default=10, le=20, ge=1, description="Number of users to return"
    ),
    q: str = Query(default="", description="Search query"),
    use_cases: UserUseCases = Depends(get_user_use_cases),
):
    query = ListUserQuery(role=role, limit=limit, search=q)

    return await use_cases.list_users.execute(query)
