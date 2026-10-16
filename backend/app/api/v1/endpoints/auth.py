"""
ARGUS — Authentication endpoints.
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
GET  /auth/me
"""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

log = structlog.get_logger()
router = APIRouter()


def _hash_token(token: str) -> str:
    """SHA-256 hash a token for safe database storage."""
    return hashlib.sha256(token.encode()).hexdigest()


async def _write_audit(
    db: AsyncSession,
    action: str,
    user_id=None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    success: bool = True,
) -> None:
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        description=description,
        ip_address=ip_address,
        success=success,
    )
    db.add(audit)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user account. First user gets ADMIN role."""
    existing = await db.execute(select(User).where(User.email == payload.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed. Please check your details.",
        )

    existing_username = await db.execute(
        select(User).where(User.username == payload.username.lower())
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration failed. Please check your details.",
        )

    user_count_result = await db.execute(select(User))
    user_count = len(user_count_result.scalars().all())
    role = UserRole.ADMIN if user_count == 0 else UserRole.VIEWER

    user = User(
        email=payload.email.lower(),
        username=payload.username.lower(),
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    ip = request.client.host if request.client else "unknown"
    await _write_audit(
        db, "USER_REGISTER", user.id, "user", user.id,
        f"New user registered: {user.email}", ip
    )

    await db.commit()
    await db.refresh(user)
    log.info("User registered", user_id=str(user.id), role=user.role)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate and return access + refresh tokens."""
    ip = request.client.host if request.client else "unknown"

    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    # Always run verification to prevent timing attacks on user enumeration
    try:
        if user:
            password_ok = verify_password(payload.password, user.hashed_password)
        else:
            # Run a dummy verification to consume similar time
            try:
                from app.core.security import hash_password as _hp
                _dummy = _hp("dummy-timing-prevention")
                verify_password("dummy", _dummy)
            except Exception:
                pass
            password_ok = False
    except Exception:
        password_ok = False

    if not password_ok or user is None:
        await _write_audit(
            db, "LOGIN_FAILURE", None, "auth", None,
            f"Failed login attempt for: {payload.email}", ip, success=False
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token_raw = create_refresh_token(subject=user.id)

    rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(refresh_token_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=ip,
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(rt)
    user.last_login_at = datetime.now(timezone.utc)

    await _write_audit(db, "LOGIN_SUCCESS", user.id, "auth", user.id, "Successful login", ip)
    await db.commit()

    log.info("User logged in", user_id=str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_raw,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Rotate a refresh token. Old token is revoked, new pair issued."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
    )

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise credentials_exception

    raw_token = auth_header.removeprefix("Bearer ").strip()

    try:
        payload = decode_token(raw_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
    except Exception:
        raise credentials_exception

    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    stored_token = result.scalar_one_or_none()

    if not stored_token or str(stored_token.user_id) != user_id:
        raise credentials_exception

    if stored_token.expires_at < datetime.now(timezone.utc):
        raise credentials_exception

    stored_token.is_revoked = True
    stored_token.revoked_at = datetime.now(timezone.utc)

    user_result = await db.execute(select(User).where(User.id == stored_token.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise credentials_exception

    new_access = create_access_token(subject=user.id, role=user.role.value)
    new_refresh_raw = create_refresh_token(subject=user.id)

    new_rt = RefreshToken(
        user_id=user.id,
        token_hash=_hash_token(new_refresh_raw),
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", ""),
    )
    db.add(new_rt)
    await db.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh_raw,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Revoke the caller's refresh token."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header.removeprefix("Bearer ").strip()
        try:
            payload = decode_token(raw_token)
            if payload.get("type") == "refresh":
                token_hash = _hash_token(raw_token)
                result = await db.execute(
                    select(RefreshToken).where(RefreshToken.token_hash == token_hash)
                )
                rt = result.scalar_one_or_none()
                if rt:
                    rt.is_revoked = True
                    rt.revoked_at = datetime.now(timezone.utc)
        except Exception:
            pass

    await _write_audit(
        db, "LOGOUT", current_user.id, "auth", current_user.id, "User logged out",
        request.client.host if request.client else "unknown"
    )
    await db.commit()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    """Return the authenticated user's profile."""
    return UserResponse.model_validate(current_user)
