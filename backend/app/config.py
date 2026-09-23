import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///chat.db")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

    MESSAGE_ENCRYPTION_KEY = os.environ.get("MESSAGE_ENCRYPTION_KEY")

    FILE_STORAGE_PATH = os.getenv("FILE_STORAGE_PATH", "./storage/attachments")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "5000"))

    ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

    ALLOWED_FILE_EXTENSIONS = {
        "jpg", "jpeg", "png", "gif", "webp",
        "pdf", "txt", "zip",
    }

    @classmethod
    def validate(cls):
        errors = []
        if not cls.JWT_SECRET_KEY:
            errors.append("JWT_SECRET_KEY is required")
        if not cls.MESSAGE_ENCRYPTION_KEY:
            errors.append("MESSAGE_ENCRYPTION_KEY is required")
        if len(cls.MESSAGE_ENCRYPTION_KEY or "") != 64:
            errors.append("MESSAGE_ENCRYPTION_KEY must be a 64-character hex string (32 bytes)")
        if errors:
            raise ValueError("Configuration errors:\n" + "\n".join(errors))
