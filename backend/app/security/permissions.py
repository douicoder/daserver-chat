from functools import wraps

import jwt as pyjwt
from flask import request, g, jsonify

from app.config import Config
from app.exceptions.exceptions import AuthenticationError, AuthorizationError
from app.database.database import SessionLocal
from app.models.user import User


def _get_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing or invalid Authorization header")
    return auth_header[7:]


def _decode_and_load_user(token: str) -> User:
    try:
        payload = pyjwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except pyjwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise AuthenticationError("User not found")
        return user
    finally:
        db.close()


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token()
        user = _decode_and_load_user(token)
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_token()
        user = _decode_and_load_user(token)
        if not user.is_admin:
            raise AuthorizationError("Admin access required")
        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def authenticate_socket(token: str) -> User:
    """Authenticate a Socket.IO connection and return the user."""
    try:
        payload = pyjwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
    except pyjwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except pyjwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if not user:
            raise AuthenticationError("User not found")
        return user
    finally:
        db.close()
