from app.domain.aggregates.session import Session
from app.domain.aggregates.users.user import UserRole
from app.domain.repositories.class_repository import ClassRepositoryInterface


async def validate_websocket_access(
    user_id: str,
    role: UserRole,
    session: Session,
    class_repo: ClassRepositoryInterface,
) -> bool:
    if role == UserRole.ADMIN:
        return True

    if role == UserRole.TEACHER:
        class_entity = await class_repo.get_by_id(session.class_id)
        if class_entity and user_id in class_entity.teacher_ids:
            return True

        return False

    if role == UserRole.STUDENT:
        return session.is_student_in_session(user_id)

    return False
