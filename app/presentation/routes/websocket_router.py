import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from fastapi.params import Depends, Query

from app.application.services.connection_manager_service import (
    ConnectionManagerServiceInterface,
)
from app.application.use_cases.sessions.commands.disconnect_session.disconnect_session_dto import (
    DisconnectSessionRequest,
)
from app.application.use_cases.sessions.commands.join_session.join_session_dto import (
    SessionJoinRequest,
)
from app.application.use_cases.sessions.queries.get_session_by_id.get_session_by_id_dto import (
    GetSessionByIdQuery,
)
from app.common.dependencies import (
    ClassUseCases,
    SessionUseCases,
    get_class_repository,
    get_class_use_cases,
    get_connection_manager_service,
    get_jwt_service,
    get_session_use_cases,
)
from app.common.utils.time_helper import TimeHelper
from app.domain.aggregates.session import Session, SessionParticipant
from app.domain.aggregates.users.user import UserRole
from app.domain.repositories.class_repository import ClassRepositoryInterface
from app.infrastructure.security.jwt_service import JwtService
from app.infrastructure.web_socket import ConnectedMessage
from app.infrastructure.web_socket.auth import validate_websocket_access

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/{session_id}/ws")
async def session_websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: str = Query(...),
    jwt_service: JwtService = Depends(get_jwt_service),
    manager: ConnectionManagerServiceInterface = Depends(
        get_connection_manager_service
    ),
    session_use_cases: SessionUseCases = Depends(get_session_use_cases),
    class_use_cases: ClassUseCases = Depends(get_class_use_cases),
    class_repository: ClassRepositoryInterface = Depends(get_class_repository),
):
    try:
        payload = jwt_service.decode(token)
        user_id = payload["user_id"]
        role = UserRole(payload["role"])
    except Exception as e:
        logger.error(f"Websocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        session = await session_use_cases.get_session_by_id_use_case.execute(
            GetSessionByIdQuery(session_id=session_id)
        )

        session_entity = Session(
            id=session.id,
            class_id=session.class_id,
            test_id=session.test_id,
            title=session.title,
            scheduled_at=session.scheduled_at,
            status=session.status,
            participants=[
                SessionParticipant(
                    student_id=p.student_id,
                    attempt_id=p.attempt_id,
                    joined_at=p.joined_at,
                    connection_status=p.connection_status,
                    last_activity=p.last_activity,
                )
                for p in session.participants
            ],
            created_by=session.created_by,
        )

        has_access = await validate_websocket_access(
            user_id=user_id,
            role=role,
            session=session_entity,
            class_repo=class_repository,
        )

        if not has_access:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.error(f"Websocket access validation failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await manager.connect(session_id=session_id, user_id=user_id, websocket=websocket)

    if role == UserRole.STUDENT:
        try:
            await session_use_cases.join_session_use_case.execute(
                SessionJoinRequest(session_id=session_id), user_id=user_id
            )
        except Exception as e:
            logger.error(f"Failed to join session: {e}")

    await websocket.send_json(
        ConnectedMessage(
            type="connected", session_id=session_id, timestamp=TimeHelper.utc_now()
        ).model_dump(mode="json")
    )

    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "heartbeat":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        logger.info(f"Websocket disconnected: {user_id}")
    except Exception as e:
        logger.error(f"Websocket error: {e}")
    finally:
        await manager.disconnect(session_id=session_id, user_id=user_id)
        if role == UserRole.STUDENT:
            try:
                await session_use_cases.disconnect_session_use_case.execute(
                    DisconnectSessionRequest(session_id=session_id),
                    user_id=user_id,
                )
            except Exception as e:
                logger.error(f"Disconnect cleanup failed: {e}")
