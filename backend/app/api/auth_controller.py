from flask import Blueprint, request, jsonify, g
from pydantic import ValidationError as PydanticError

from app.dto.auth_dto import LoginRequest
from app.dto.user_dto import RegisterRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.security.permissions import require_auth
from app.exceptions.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    AuthenticationError,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
auth_service = AuthService()
user_service = UserService()


@auth_bp.errorhandler(PydanticError)
def handle_validation_error(e):
    return jsonify({"error": {"code": "VALIDATION_ERROR", "message": str(e)}}), 400


@auth_bp.errorhandler(UserAlreadyExistsError)
def handle_user_exists(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 409


@auth_bp.errorhandler(InvalidCredentialsError)
def handle_invalid_credentials(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 401


@auth_bp.errorhandler(AuthenticationError)
def handle_auth_error(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 401


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    dto = RegisterRequest(**data)
    result = auth_service.register(dto.username, dto.password)
    return jsonify(result), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    dto = LoginRequest(**data)
    result = auth_service.login(dto.username, dto.password)
    return jsonify(result), 200


@auth_bp.route("/me", methods=["GET"])
@require_auth
def me():
    user = user_service.get_user(g.current_user.id)
    return jsonify(user), 200
