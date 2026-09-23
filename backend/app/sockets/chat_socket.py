import logging

from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

from app.security.permissions import authenticate_socket
from app.services.message_service import MessageService
from app.dto.message_dto import SendMessageRequest
from app.exceptions.exceptions import (
    AuthenticationError,
    ValidationError,
    AttachmentError,
    ConversationNotFoundError,
    NotConversationMemberError,
    ConversationError,
)
from pydantic import ValidationError as PydanticError

logger = logging.getLogger(__name__)

socketio = SocketIO()
message_service = MessageService()

# Track authenticated users: sid -> user
connected_users = {}


def add_sids_to_conversation(conversation_id: str, user_ids: list[str]) -> None:
    """Join all currently-connected sockets of the given users to a room.

    Called from REST controllers right after a conversation is created (or a
    member is added) so the sender AND the recipient immediately receive
    real-time events without having to reconnect/refresh.
    """
    if not user_ids:
        return
    wanted = set(user_ids)
    for sid, user in list(connected_users.items()):
        try:
            if getattr(user, "id", None) in wanted:
                socketio.server.enter_room(sid, f"conversation:{conversation_id}")
        except Exception:
            continue


def remove_sids_from_conversation(conversation_id: str, user_ids: list[str]) -> None:
    if not user_ids:
        return
    wanted = set(user_ids)
    for sid, user in list(connected_users.items()):
        try:
            if getattr(user, "id", None) in wanted:
                socketio.server.leave_room(sid, f"conversation:{conversation_id}")
        except Exception:
            continue


def _member_ids(conversation_id: str) -> list[str]:
    from app.database.database import SessionLocal
    from app.repositories.conversation_repository import ConversationRepository

    db = SessionLocal()
    try:
        repo = ConversationRepository(db)
        conv = repo.find_by_id(conversation_id)
        if not conv or not conv.members:
            return []
        return [m.user_id for m in conv.members]
    finally:
        db.close()


def _user_rooms(user_id: str) -> list[str]:
    from app.database.database import SessionLocal
    from app.repositories.conversation_repository import ConversationRepository

    db = SessionLocal()
    try:
        repo = ConversationRepository(db)
        return [f"conversation:{c.id}" for c in repo.list_for_user(user_id)]
    finally:
        db.close()


@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")
    if not token:
        logger.warning("Socket connection rejected: no token")
        return False

    try:
        user = authenticate_socket(token)
        connected_users[request.sid] = user
        for room in _user_rooms(user.id):
            join_room(room)
        logger.info("User connected: %s (sid=%s)", user.username, request.sid)
    except AuthenticationError as e:
        logger.warning("Socket authentication failed: %s", e.message)
        return False


@socketio.on("disconnect")
def handle_disconnect():
    user = connected_users.pop(request.sid, None)
    if user:
        for room in _user_rooms(user.id):
            leave_room(room)
        logger.info("User disconnected: %s (sid=%s)", user.username, request.sid)


@socketio.on("join_conversation")
def handle_join_conversation(data):
    """Allow clients to join a newly created conversation room without reconnecting."""
    user = connected_users.get(request.sid)
    if not user:
        emit("error", {"code": "AUTHENTICATION_ERROR", "message": "Not authenticated"})
        return
    conversation_id = (data or {}).get("conversation_id")
    if not conversation_id:
        return
    from app.database.database import SessionLocal
    from app.repositories.conversation_repository import ConversationRepository

    db = SessionLocal()
    try:
        if ConversationRepository(db).is_member(conversation_id, user.id):
            join_room(f"conversation:{conversation_id}")
    finally:
        db.close()


@socketio.on("send_message")
def handle_send_message(data):
    user = connected_users.get(request.sid)
    if not user:
        emit("error", {"code": "AUTHENTICATION_ERROR", "message": "Not authenticated"})
        return

    try:
        dto = SendMessageRequest(**(data or {}))
    except (PydanticError, ValueError) as e:
        emit("error", {"code": "VALIDATION_ERROR", "message": str(e)})
        return

    if not dto.conversation_id:
        emit("error", {"code": "VALIDATION_ERROR", "message": "conversation_id is required"})
        return

    try:
        result = message_service.send_message(
            sender_id=user.id,
            content=dto.content,
            attachment_id=dto.attachment_id,
            conversation_id=dto.conversation_id,
        )
        room = f"conversation:{dto.conversation_id}"
        # Heal room membership: the sender may have created this conversation
        # after (re)connecting and never joined the room, so make sure the
        # sender's socket is in the room before broadcasting.
        try:
            join_room(room)
        except Exception:
            pass
        emit(
            "receive_message",
            result,
            to=room,
        )
        # Guarantee delivery even when the recipient's socket has not joined
        # the (newly created) room yet: emit directly to every connected
        # socket of each conversation member. Frontend dedupes by message id,
        # so duplicates for sockets already in the room are harmless.
        try:
            member_ids = set(_member_ids(dto.conversation_id))
            for sid, u in list(connected_users.items()):
                if sid == request.sid:
                    continue
                if getattr(u, "id", None) in member_ids:
                    emit("receive_message", result, to=sid)
            # Always echo back to the sender directly so the first message in
            # a brand-new conversation shows up instantly without refresh.
            emit("receive_message", result, to=request.sid)
        except Exception:
            pass
    except (
        ValidationError,
        AttachmentError,
        ConversationNotFoundError,
        NotConversationMemberError,
        ConversationError,
    ) as e:
        emit("error", {"code": e.code, "message": e.message})
