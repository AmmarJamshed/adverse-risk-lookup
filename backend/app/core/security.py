"""Security utilities: password hashing, JWT, RBAC helpers."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "super_admin": ["*"],
    "admin": [
        "users:read",
        "users:write",
        "feeds:read",
        "feeds:write",
        "risks:read",
        "risks:write",
        "articles:read",
        "articles:write",
        "alerts:read",
        "alerts:write",
        "reports:read",
        "reports:write",
        "admin:read",
        "admin:write",
        "audit:read",
        "assistant:use",
    ],
    "risk_manager": [
        "risks:read",
        "risks:write",
        "articles:read",
        "alerts:read",
        "alerts:write",
        "reports:read",
        "reports:write",
        "assistant:use",
        "feeds:read",
    ],
    "compliance": [
        "risks:read",
        "articles:read",
        "alerts:read",
        "reports:read",
        "assistant:use",
    ],
    "cybersecurity": [
        "risks:read",
        "articles:read",
        "alerts:read",
        "reports:read",
        "assistant:use",
    ],
    "auditor": [
        "risks:read",
        "articles:read",
        "reports:read",
        "audit:read",
        "assistant:use",
    ],
    "viewer": [
        "risks:read",
        "articles:read",
        "alerts:read",
        "reports:read",
        "assistant:use",
    ],
}


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    extra: Optional[dict[str, Any]] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_expire_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def has_permission(role: str, permission: str) -> bool:
    perms = ROLE_PERMISSIONS.get(role, [])
    if "*" in perms:
        return True
    return permission in perms


class TokenError(Exception):
    pass


def safe_decode(token: str) -> dict[str, Any]:
    try:
        return decode_access_token(token)
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc
