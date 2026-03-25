"""Token management: JWT creation, refresh, Facebook token health."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import jwt, JWTError

from app.config import get_settings

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 1
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    settings = get_settings()
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT. Raises JWTError on invalid/expired."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def verify_access_token(token: str) -> Optional[str]:
    """Returns user_id if token is valid, None otherwise."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        return payload.get("user_id")
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[str]:
    """Returns user_id if refresh token is valid, None otherwise."""
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            return None
        return payload.get("user_id")
    except JWTError:
        return None
