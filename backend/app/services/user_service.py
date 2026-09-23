from app.database.database import SessionLocal
from app.repositories.user_repository import UserRepository


class UserService:
    def get_user(self, user_id: str) -> dict | None:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            user = user_repo.find_by_id(user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "is_admin": user.is_admin,
            }
        finally:
            db.close()

    def search_users(self, query: str = "", exclude_user_id: str | None = None) -> list[dict]:
        db = SessionLocal()
        try:
            user_repo = UserRepository(db)
            users = user_repo.search_by_username(query or "", exclude_user_id=exclude_user_id)
            return [{"id": u.id, "username": u.username} for u in users]
        finally:
            db.close()
