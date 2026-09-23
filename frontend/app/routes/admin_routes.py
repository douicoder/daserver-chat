from flask import Blueprint, request, jsonify, session
from app.services.backend_client import BackendClient

admin_bp = Blueprint("admin_api", __name__)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if "access_token" not in session:
            return jsonify({"error": {"code": "AUTHENTICATION_ERROR", "message": "Not authenticated"}}), 401
        user = session.get("user", {})
        if not user.get("is_admin"):
            return jsonify({"error": {"code": "AUTHORIZATION_ERROR", "message": "Admin access required"}}), 403
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/api/admin/users", methods=["GET"])
@admin_required
def get_users():
    token = session["access_token"]
    client = BackendClient()
    status, body = client.admin_get_users(token)
    return jsonify(body), status


@admin_bp.route("/api/admin/users/<user_id>/password", methods=["POST"])
@admin_required
def change_password(user_id):
    token = session["access_token"]
    data = request.get_json(silent=True) or {}
    new_password = data.get("new_password", "")

    if not new_password or len(new_password) < 6:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Password must be at least 6 characters."}}), 400

    client = BackendClient()
    status, body = client.admin_change_password(token, user_id, new_password)
    return jsonify(body), status
