"""
ARGUS — Security utilities: password hashing, JWT tokens.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Argon2id is the recommended password hashing algorithm (PHC winner)
# passlib may warn about missing bcrypt on Python 3.14 — argon2 is our only scheme
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    pwd_context = CryptContext(
        schemes=["argon2"],
        deprecated="auto",
        argon2__memory_cost=65536,   # 64 MiB
        argon2__time_cost=3,
        argon2__parallelism=4,
    )


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using Argon2id."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: str | UUID,
    role: str,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        subject: The user identifier (UUID string).
        role: The user's role, embedded in the token.
        additional_claims: Optional extra claims to include.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if additional_claims:
        payload.update(additional_claims)

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | UUID) -> str:
    """
    Create a longer-lived JWT refresh token.

    Refresh tokens are stored in the database so they can be revoked.
    They must NOT be stored in localStorage on the client.

    Args:
        subject: The user identifier (UUID string).

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
