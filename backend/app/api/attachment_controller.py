import os
from flask import Blueprint, request, jsonify, g, send_file

from app.services.attachment_service import AttachmentService
from app.security.permissions import require_auth
from app.exceptions.exceptions import AttachmentError, FileTooLargeError, UnsupportedFileTypeError

attachment_bp = Blueprint("attachments", __name__, url_prefix="/api/attachments")
attachment_service = AttachmentService()


@attachment_bp.errorhandler(AttachmentError)
def handle_attachment_error(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 400


@attachment_bp.errorhandler(FileTooLargeError)
def handle_file_too_large(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 413


@attachment_bp.errorhandler(UnsupportedFileTypeError)
def handle_unsupported_type(e):
    return jsonify({"error": {"code": e.code, "message": e.message}}), 415


@attachment_bp.route("", methods=["POST"])
@require_auth
def upload():
    if "file" not in request.files:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "No file provided"}}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "No file selected"}}), 400

    from werkzeug.utils import secure_filename
    original_filename = secure_filename(file.filename)
    if not original_filename:
        return jsonify({"error": {"code": "VALIDATION_ERROR", "message": "Invalid filename"}}), 400

    file_bytes = file.read()
    result = attachment_service.upload(file_bytes, original_filename, g.current_user.id)
    return jsonify(result), 201


@attachment_bp.route("/<attachment_id>", methods=["GET"])
@require_auth
def download(attachment_id):
    result = attachment_service.stream_file(attachment_id)
    if not result:
        return jsonify({"error": {"code": "ATTACHMENT_ERROR", "message": "Attachment not found"}}), 404

    file_path, original_filename, mime_type = result
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=original_filename,
    )
