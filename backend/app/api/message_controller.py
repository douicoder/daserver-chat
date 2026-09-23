from flask import Blueprint, request, jsonify, g

from app.services.message_service import MessageService
from app.security.permissions import require_auth
from app.exceptions.exceptions import ValidationError

message_bp = Blueprint("messages", __name__, url_prefix="/api/messages")
message_service = MessageService()


@message_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 400


@message_bp.route("", methods=["GET"])
@require_auth
def get_messages():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 50, type=int)

    if page < 1:
        page = 1
    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100

    result = message_service.get_messages(page, limit)
    return jsonify(result), 200
