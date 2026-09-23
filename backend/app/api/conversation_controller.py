from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError as PydanticError

from app.dto.conversation_dto import (
    AddConversationMemberRequest,
    CreateDirectConversationRequest,
    CreateGroupConversationRequest,
    UpdateGroupRequest,
)
from app.dto.message_dto import SendMessageRequest
from app.services.conversation_service import ConversationService
from app.services.message_service import MessageService
from app.security.permissions import require_auth
from app.exceptions.exceptions import (
    AuthenticationError,
    ConversationError,
    ConversationNotFoundError,
    NotConversationMemberError,
    NotGroupOwnerError,
    UserNotFoundError,
    ValidationError,
)

conversation_bp = Blueprint("conversations", __name__, url_prefix="/api/conversations")
conversation_service = ConversationService()
message_service = MessageService()


@conversation_bp.errorhandler(PydanticError)
def handle_pydantic_error(e):
    return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400


@conversation_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 400


@conversation_bp.errorhandler(ConversationError)
def handle_conversation_error(e):
    status = 409 if e.code in ("USER_ALREADY_MEMBER",) else 400
    return jsonify({"error": {"code": e.code, "message": e.message}}), status


@conversation_bp.errorhandler(ConversationNotFoundError)
def handle_not_found(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 404


@conversation_bp.errorhandler(NotConversationMemberError)
def handle_not_member(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 403


@conversation_bp.errorhandler(NotGroupOwnerError)
def handle_not_owner(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 403


@conversation_bp.errorhandler(UserNotFoundError)
def handle_user_not_found(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 404


@conversation_bp.errorhandler(AuthenticationError)
def handle_auth_error(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 401


@conversation_bp.route("", methods=["GET"])
@require_auth
def list_conversations():
    result = conversation_service.list_conversations(g.current_user.id)
    return jsonify(result), 200


@conversation_bp.route("/<conversation_id>", methods=["GET"])
@require_auth
def get_conversation(conversation_id):
    result = conversation_service.get_conversation(g.current_user.id, conversation_id)
    return jsonify(result), 200


@conversation_bp.route("/direct", methods=["POST"])
@require_auth
def create_direct():
    dto = CreateDirectConversationRequest(**(request.get_json() or {}))
    result, created = conversation_service.create_direct(g.current_user.id, dto.user_id)
    if created:
        try:
            from app.sockets.chat_socket import add_sids_to_conversation
            member_ids = [m["id"] for m in result.get("members", [])] or [g.current_user.id, dto.user_id]
            add_sids_to_conversation(result["id"], member_ids)
        except Exception:
            pass
    return jsonify(result), 201 if created else 200


@conversation_bp.route("/group", methods=["POST"])
@require_auth
def create_group():
    dto = CreateGroupConversationRequest(**(request.get_json() or {}))
    result = conversation_service.create_group(g.current_user.id, dto.name, dto.member_ids)
    try:
        from app.sockets.chat_socket import add_sids_to_conversation
        member_ids = [m["id"] for m in result.get("members", [])]
        add_sids_to_conversation(result["id"], member_ids)
    except Exception:
        pass
    return jsonify(result), 201


@conversation_bp.route("/<conversation_id>", methods=["PATCH"])
@require_auth
def rename_group(conversation_id):
    dto = UpdateGroupRequest(**(request.get_json() or {}))
    result = conversation_service.rename_group(g.current_user.id, conversation_id, dto.name)
    return jsonify(result), 200


@conversation_bp.route("/<conversation_id>/members", methods=["POST"])
@require_auth
def add_member(conversation_id):
    dto = AddConversationMemberRequest(**(request.get_json() or {}))
    result = conversation_service.add_member(g.current_user.id, conversation_id, dto.user_id)
    try:
        from app.sockets.chat_socket import add_sids_to_conversation
        add_sids_to_conversation(conversation_id, [dto.user_id])
    except Exception:
        pass
    return jsonify(result), 200


@conversation_bp.route("/<conversation_id>/members/<user_id>", methods=["DELETE"])
@require_auth
def remove_member(conversation_id, user_id):
    result = conversation_service.remove_member(g.current_user.id, conversation_id, user_id)
    try:
        from app.sockets.chat_socket import remove_sids_from_conversation
        remove_sids_from_conversation(conversation_id, [user_id])
    except Exception:
        pass
    return jsonify(result), 200


@conversation_bp.route("/<conversation_id>/leave", methods=["POST"])
@require_auth
def leave_group(conversation_id):
    conversation_service.leave_group(g.current_user.id, conversation_id)
    return jsonify({"message": "You have left the group"}), 200


@conversation_bp.route("/<conversation_id>/messages", methods=["GET"])
@require_auth
def get_conversation_messages(conversation_id):
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)
    if page < 1:
        page = 1
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    result = message_service.get_conversation_messages(
        g.current_user.id, conversation_id, page, limit
    )
    return jsonify(result), 200


@conversation_bp.route("/<conversation_id>/messages", methods=["POST"])
@require_auth
def send_conversation_message(conversation_id):
    dto = SendMessageRequest(**(request.get_json() or {}))
    result = message_service.send_message(
        sender_id=g.current_user.id,
        content=dto.content,
        attachment_id=dto.attachment_id,
        conversation_id=conversation_id,
    )
    return jsonify(result), 201
