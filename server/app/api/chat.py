import json
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models.models import ChatMessageModel, UserModel
from app.repositories.sqlalchemy import ChatRepository, UserRepository
from app.schemas.chat import ChatMessage, ChatMessageCreate, ChatUser
from app.services.audit import AuditService

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        sockets = self._connections.get(user_id)
        if not sockets:
            return
        sockets.discard(websocket)
        if not sockets:
            self._connections.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        return user_id in self._connections

    async def send_to_user(self, user_id: int, payload: dict[str, Any]) -> None:
        sockets = list(self._connections.get(user_id, set()))
        for socket in sockets:
            try:
                await socket.send_json(payload)
            except RuntimeError:
                self.disconnect(user_id, socket)


manager = ChatConnectionManager()


def serialize_message(message: ChatMessageModel, sender: UserModel, receiver: UserModel) -> ChatMessage:
    return ChatMessage(
        id=message.id,
        sender_id=message.sender_id,
        sender_name=sender.username,
        receiver_id=message.receiver_id,
        receiver_name=receiver.username,
        content=message.content,
        is_read=message.is_read,
        created_at=message.created_at,
    )


def authenticate_websocket_user(websocket: WebSocket, settings: Settings, db: Session) -> UserModel | None:
    token = websocket.query_params.get("token", "")
    try:
        user_id = decode_access_token(token, settings)
    except AppError:
        return None
    user = db.get(UserModel, int(user_id)) if user_id.isdigit() else None
    if user is None or not user.enabled:
        return None
    return user


@router.get("/users", response_model=list[ChatUser])
def list_chat_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> list[ChatUser]:
    users = ChatRepository(db).list_chat_users(current_user)
    return [
        ChatUser(
            id=user.id,
            username=user.username,
            role=user.role,
            enabled=user.enabled,
            online=manager.is_online(user.id),
        )
        for user in users
    ]


@router.get("/history/{peer_id}", response_model=list[ChatMessage])
def get_chat_history(
    peer_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> list[ChatMessage]:
    peer = UserRepository(db).get_by_id(peer_id)
    if peer is None or not peer.enabled:
        raise AppError("USER_NOT_FOUND", "聊天用户不存在或已停用", 404)
    repo = ChatRepository(db)
    messages = repo.get_history(current_user, peer_id)
    repo.mark_conversation_read(current_user, peer_id)
    users = {current_user.id: current_user, peer.id: peer}
    return [serialize_message(message, users[message.sender_id], users[message.receiver_id]) for message in messages]


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket) -> None:
    settings: Settings = websocket.app.state.settings
    session_factory = websocket.app.state.session_factory
    db: Session = session_factory()
    current_user = authenticate_websocket_user(websocket, settings, db)
    if current_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        db.close()
        return

    await manager.connect(current_user.id, websocket)
    await websocket.send_json({"type": "system", "message": "聊天连接已建立"})
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                payload = json.loads(raw_data)
                data = ChatMessageCreate.model_validate(payload)
            except (json.JSONDecodeError, ValidationError):
                await websocket.send_json({"type": "error", "message": "消息格式不正确"})
                continue

            receiver = UserRepository(db).get_by_id(data.receiver_id)
            if receiver is None or not receiver.enabled:
                await websocket.send_json({"type": "error", "message": "接收用户不存在或已停用"})
                continue
            if receiver.id == current_user.id:
                await websocket.send_json({"type": "error", "message": "不能给自己发送消息"})
                continue

            message = ChatRepository(db).create_message(current_user, receiver, data.content)
            AuditService(db).record(
                "chat_send",
                "success",
                user=current_user,
                detail=f"receiver={receiver.username}, message_id={message.id}",
            )
            serialized = serialize_message(message, current_user, receiver).model_dump(mode="json")
            event = {"type": "message", "message": serialized}
            await manager.send_to_user(receiver.id, event)
            await manager.send_to_user(current_user.id, event)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(current_user.id, websocket)
        db.close()
