import os
import sys
import getpass
import logging

from app.config import Config
from app import create_app
from app.database.database import SessionLocal, init_db
from app.models.user import User
from app.security.password import hash_password


def create_admin():
    """CLI command to create an admin user."""
    Config.validate()
    init_db()

    print("Create Admin User")
    print("-" * 40)

    username = input("Username: ").strip()
    if not username:
        print("Error: Username cannot be empty")
        sys.exit(1)

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("Error: Passwords do not match")
        sys.exit(1)

    if len(password) < 6:
        print("Error: Password must be at least 6 characters")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Error: User '{username}' already exists")
            sys.exit(1)

        user = User(
            username=username,
            password_hash=hash_password(password),
            is_admin=True,
        )
        db.add(user)
        db.commit()
        print(f"Admin user '{username}' created successfully")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create-admin":
        create_admin()
    else:
        app = create_app()
        from app.sockets.chat_socket import socketio
        socketio.run(app, host="0.0.0.0", port=5000, debug=True)
