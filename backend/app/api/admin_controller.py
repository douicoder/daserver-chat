from flask import Blueprint, request, jsonify

from app.dto.admin_dto import ChangePasswordRequest
from app.services.admin_service import AdminService
from app.security.permissions import require_admin
from app.exceptions.exceptions import UserNotFoundError

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")
admin_service = AdminService()


@admin_bp.errorhandler(UserNotFoundError)
def handle_user_not_found(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 404


@admin_bp.route("/users", methods=["GET"])
@require_admin
def list_users():
    users = admin_service.list_users()
    return jsonify(users), 200


@admin_bp.route("/users/<user_id>/password", methods=["POST"])
@require_admin
def change_password(user_id):
    data = request.get_json()
    dto = ChangePasswordRequest(**data)
    result = admin_service.change_password(user_id, dto.new_password)
    return jsonify(result), 200
