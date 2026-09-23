import os
import uuid
import secrets

from app.config import Config
from app.exceptions.exceptions import FileTooLargeError, UnsupportedFileTypeError


def _ensure_storage_dir():
    os.makedirs(Config.FILE_STORAGE_PATH, exist_ok=True)


def generate_stored_filename(original_filename: str) -> str:
    ext = os.path.splitext(original_filename)[1].lower()
    random_name = secrets.token_hex(16)  # 32-char hex string
    return f"{random_name}{ext}"


def validate_file(file_bytes: bytes, filename: str) -> tuple[str, int]:
    """Validate file size and extension. Returns (mime_type, size)."""
    size = len(file_bytes)

    if size > Config.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileTooLargeError(f"File exceeds maximum size of {Config.MAX_FILE_SIZE_MB}MB")

    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext not in Config.ALLOWED_FILE_EXTENSIONS:
        raise UnsupportedFileTypeError(f"File type '.{ext}' is not allowed")

    mime_type = _detect_mime_type(file_bytes, ext)
    return mime_type, size


def _detect_mime_type(file_bytes: bytes, ext: str) -> str:
    """Detect MIME type from file content/signature with extension fallback."""
    if file_bytes[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if file_bytes[:4] == b"\x89PNG":
        return "image/png"
    if file_bytes[:4] == b"GIF8":
        return "image/gif"
    if file_bytes[:4] == b"RIFF" and file_bytes[8:12] == b"WEBP":
        return "image/webp"
    if file_bytes[:4] == b"%PDF":
        return "application/pdf"
    if file_bytes[:4] == b"PK\x03\x04":
        return "application/zip"

    extension_map = {
        "txt": "text/plain",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "pdf": "application/pdf",
        "zip": "application/zip",
    }
    return extension_map.get(ext, "application/octet-stream")


def save_file(file_bytes: bytes, stored_filename: str) -> str:
    """Save file to storage. Returns the full storage path."""
    _ensure_storage_dir()
    full_path = os.path.join(Config.FILE_STORAGE_PATH, stored_filename)
    real_storage = os.path.realpath(Config.FILE_STORAGE_PATH)
    real_target = os.path.realpath(os.path.dirname(full_path))

    if not real_target.startswith(real_storage):
        raise ValueError("Path traversal detected")

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return full_path


def get_file_path(stored_filename: str) -> str:
    """Get full path for a stored file, with traversal protection."""
    full_path = os.path.join(Config.FILE_STORAGE_PATH, stored_filename)
    real_storage = os.path.realpath(Config.FILE_STORAGE_PATH)
    real_target = os.path.realpath(full_path)

    if not real_target.startswith(real_storage):
        raise ValueError("Path traversal detected")

    return real_target


def file_exists(stored_filename: str) -> bool:
    path = get_file_path(stored_filename)
    return os.path.isfile(path)
