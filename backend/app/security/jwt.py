from datetime import datetime, timedelta, timezone

import jwt

from app.config import Config


def create_access_token(user_id: str, username: str, is_admin: bool) -> dict:
    exp_minutes = Config.JWT_EXPIRATION_MINUTES
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=exp_minutes)

    payload = {
        "sub": user_id,
        "username": username,
        "is_admin": is_admin,
        "iat": now,
        "exp": exp,
    }

    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "expires_at": exp.isoformat()}


def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
