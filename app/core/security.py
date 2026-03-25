from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def is_password_strong(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""


def _create_token(data: dict[str, Any], expires_delta: timedelta) -> tuple[str, datetime, str]:
    payload = data.copy()
    jti = payload.get("jti") or str(uuid4())
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload["jti"] = jti
    payload["exp"] = expires_at
    payload["iat"] = datetime.now(timezone.utc)
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm), expires_at, jti


def create_access_token(subject: str | int, extra: Optional[dict] = None) -> tuple[str, datetime, str]:
    data: dict[str, Any] = {"sub": str(subject), "type": "access"}
    if extra:
        data.update(extra)
    return _create_token(data, timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(subject: str | int, extra: Optional[dict] = None) -> tuple[str, datetime, str]:
    data: dict[str, Any] = {"sub": str(subject), "type": "refresh"}
    if extra:
        data.update(extra)
    return _create_token(data, timedelta(days=settings.refresh_token_expire_days))


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def verify_token_type(token: str, expected_type: str) -> dict[str, Any]:
    payload = decode_token(token)
    if payload.get("type") != expected_type:
        raise JWTError(f"Expected {expected_type} token, got {payload.get('type')}")
    return payload
