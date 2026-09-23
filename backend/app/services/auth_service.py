import logging

from app.database.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token
from app.exceptions.exceptions import (
    UserAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)

logger = logging.getLogger(__name__)


class AuthService:
    def register(self, username: str, password: str) -> dict:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)

            if user_repo.find_by_username(username):
                raise UserAlreadyExistsError("Username already taken")

            password_hash = hash_password(password)
            user = user_repo.create(username=username, password_hash=password_hash)

            logger.info("User registered: %s", username)
            token_data = create_access_token(user.id, user.username, user.is_admin)
            return {
                **token_data,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_admin": user.is_admin,
                },
            }
        finally:
            db.close()

    def login(self, username: str, password: str) -> dict:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.find_by_username(username)

            if not user or not verify_password(password, user.password_hash):
                logger.warning("Failed login attempt for username: %s", username)
                raise InvalidCredentialsError()

            token_data = create_access_token(user.id, user.username, user.is_admin)
            return {
                **token_data,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "is_admin": user.is_admin,
                },
            }
        finally:
            db.close()
