import logging

from app.database.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.security.password import hash_password
from app.exceptions.exceptions import UserNotFoundError

logger = logging.getLogger(__name__)


class AdminService:
    def list_users(self) -> list[dict]:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            users = user_repo.list_all()
            return [
                {
                    "id": u.id,
                    "username": u.username,
                    "is_admin": u.is_admin,
                    "created_at": u.created_at.isoformat(),
                }
                for u in users
            ]
        finally:
            db.close()

    def change_password(self, user_id: str, new_password: str) -> dict:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            new_hash = hash_password(new_password)
            user = user_repo.update_password(user_id, new_hash)

            if not user:
                raise UserNotFoundError("User not found")

            logger.info("Admin changed password for user %s", user_id)
            return {"message": "Password updated successfully"}
        finally:
            db.close()
