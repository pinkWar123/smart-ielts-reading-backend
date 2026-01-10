from typing import List

from fastapi import Depends, HTTPException
from starlette import status

from app.domain.aggregates.users.user import UserRole
from app.presentation.security.auth_security import verify_token


class RequireRoles:
    def __init__(self, roles: List[str]):
        self.roles = roles

    def __call__(self, current_user: dict = Depends(verify_token)) -> dict:
        # current_user is a decoded JWT payload (dict), not a User object
        user_role = current_user.get("role")
        if user_role not in self.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(self.roles)}",
            )
        return current_user


require_auth = Depends(verify_token)
required_admin = RequireRoles([UserRole.ADMIN.value])
require_student = RequireRoles([UserRole.STUDENT.value])
