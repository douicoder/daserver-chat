from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def find_by_id(self, user_id: str) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, username: str, password_hash: str, is_admin: bool = False) -> User:
        user = User(username=username, password_hash=password_hash, is_admin=is_admin)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self) -> list[User]:
        return self.db.query(User).order_by(User.created_at.asc()).all()

    def search_by_username(self, query: str, exclude_user_id: str | None = None, limit: int = 20) -> list[User]:
        q = self.db.query(User).filter(User.username.ilike(f"%{query}%"))
        if exclude_user_id:
            q = q.filter(User.id != exclude_user_id)
        return q.order_by(User.username.asc()).limit(limit).all()

    def update_password(self, user_id: str, new_password_hash: str) -> User | None:
        user = self.find_by_id(user_id)
        if user:
            user.password_hash = new_password_hash
            self.db.commit()
            self.db.refresh(user)
        return user
