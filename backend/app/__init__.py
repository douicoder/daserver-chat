import logging
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.database.database import init_db
from app.api import auth_bp, user_bp, message_bp, attachment_bp, admin_bp, conversation_bp
from app.sockets.chat_socket import socketio
from app.exceptions.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    UserAlreadyExistsError,
    UserNotFoundError,
    InvalidCredentialsError,
    MessageError,
    AttachmentError,
    FileTooLargeError,
    UnsupportedFileTypeError,
    ConversationNotFoundError,
    NotConversationMemberError,
    NotGroupOwnerError,
    ConversationError,
)


def create_app():
    Config.validate()

    app = Flask(__name__)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    CORS(app, origins=Config.ALLOWED_ORIGINS)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(message_bp)
    app.register_blueprint(attachment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(conversation_bp)

    # Initialize Socket.IO
    socketio.init_app(app, cors_allowed_origins=Config.ALLOWED_ORIGINS)

    # Register global error handlers
    @app.errorhandler(AuthenticationError)
    def handle_auth_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 401

    @app.errorhandler(AuthorizationError)
    def handle_authz_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 403

    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 400

    @app.errorhandler(UserAlreadyExistsError)
    def handle_user_exists(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 409

    @app.errorhandler(UserNotFoundError)
    def handle_user_not_found(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 404

    @app.errorhandler(InvalidCredentialsError)
    def handle_invalid_creds(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 401

    @app.errorhandler(MessageError)
    def handle_message_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 400

    @app.errorhandler(AttachmentError)
    def handle_attachment_error(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 400

    @app.errorhandler(FileTooLargeError)
    def handle_file_too_large(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 413

    @app.errorhandler(UnsupportedFileTypeError)
    def handle_unsupported_type(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 415

    @app.errorhandler(ConversationNotFoundError)
    def handle_conversation_not_found(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 404

    @app.errorhandler(NotConversationMemberError)
    def handle_not_conversation_member(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 403

    @app.errorhandler(NotGroupOwnerError)
    def handle_not_group_owner(e):
        return jsonify({"error": {"code": e.code, "message": e.message}}), 403

    @app.errorhandler(ConversationError)
    def handle_conversation_error(e):
        status = 409 if e.code == "USER_ALREADY_MEMBER" else 400
        return jsonify({"error": {"code": e.code, "message": e.message}}), status

    init_db()
    logging.getLogger(__name__).info("Chat backend started")

    return app
