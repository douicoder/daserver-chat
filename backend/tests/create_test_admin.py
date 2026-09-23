import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.database import SessionLocal
from app.models.user import User
from app.security.password import hash_password

db = SessionLocal()
existing = db.query(User).filter(User.username == "admin_e2e").first()
if not existing:
    admin = User(
        username="admin_e2e",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    print("admin created")
else:
    print("admin already exists")
db.close()
