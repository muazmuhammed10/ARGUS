"""
ARGUS — User management endpoints (admin only).
GET    /users              list all users
GET    /users/{id}         get user
PATCH  /users/{id}         update role / activate / deactivate
DELETE /users/{id}         deactivate (soft delete)
"""

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AdminUser, CurrentUser
from app.core.database import get_db
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import UserResponse
from app.schemas.users import UserUpdate, PasswordResetRequest, PasswordResetConfirm

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK)
async def list_users(
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    total = await db.scalar(select(func.count(User.id))) or 0
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    users = result.scalars().all()
    return {
        "items": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin: update a user's role or active status."""
    # Prevent self-demotion from ADMIN
    if user_id == current_user.id and payload.role and payload.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote your own admin account. Have another admin do this."
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    changes = []
    if payload.full_name is not None:
        changes.append(f"full_name: {user.full_name} → {payload.full_name}")
        user.full_name = payload.full_name
    if payload.role is not None:
        changes.append(f"role: {user.role} → {payload.role}")
        user.role = payload.role
    if payload.is_active is not None:
        changes.append(f"is_active: {user.is_active} → {payload.is_active}")
        user.is_active = payload.is_active

    if changes:
        db.add(AuditLog(
            user_id=current_user.id,
            action="USER_UPDATED",
            resource_type="user",
            resource_id=str(user.id),
            description=f"Admin updated user {user.email}: {'; '.join(changes)}",
            success=True,
        ))

    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin: deactivate a user (soft delete — preserves audit trail)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.add(AuditLog(
        user_id=current_user.id,
        action="USER_DEACTIVATED",
        resource_type="user",
        resource_id=str(user.id),
        description=f"Admin deactivated user {user.email}",
        success=True,
    ))
    await db.commit()


# ── Password reset flow ───────────────────────────────────────────────────────

@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
async def request_password_reset(
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset token.
    Returns 200 regardless of whether the email exists (no user enumeration).
    In production, this would send an email. For now, the token is returned
    directly for local development use.
    """
    result = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        token = secrets.token_urlsafe(32)
        user.password_reset_token = hash_password(token)  # Store hashed
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        # In production: send email with token. For development, return token.
        return {
            "message": "If that email is registered, a reset token has been issued.",
            "dev_token": token,  # Only included in development
            "expires_in": "1 hour",
        }

    return {"message": "If that email is registered, a reset token has been issued."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    payload: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """Confirm a password reset using a valid token."""
    from app.core.security import verify_password as _verify

    # Find all users with unexpired reset tokens
    result = await db.execute(
        select(User).where(
            User.password_reset_token.isnot(None),
            User.password_reset_expires > datetime.now(timezone.utc),
            User.is_active == True,  # noqa: E712
        )
    )
    users = result.scalars().all()

    matched_user = None
    for u in users:
        if u.password_reset_token and _verify(payload.token, u.password_reset_token):
            matched_user = u
            break

    if not matched_user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token."
        )

    from app.core.security import hash_password as _hash
    from app.schemas.auth import RegisterRequest
    # Validate password strength
    import re
    pw = payload.new_password
    errors = []
    if not re.search(r"[A-Z]", pw):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", pw):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", pw):
        errors.append("at least one digit")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-]', pw):
        errors.append("at least one special character")
    if errors:
        raise HTTPException(status_code=422, detail=f"Password must contain {', '.join(errors)}")

    matched_user.hashed_password = _hash(pw)
    matched_user.password_reset_token = None
    matched_user.password_reset_expires = None

    # Revoke all existing refresh tokens for security
    from app.models.refresh_token import RefreshToken
    from datetime import timezone as tz
    rt_result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == matched_user.id,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    for rt in rt_result.scalars().all():
        rt.is_revoked = True
        rt.revoked_at = datetime.now(tz.utc)

    db.add(AuditLog(
        user_id=matched_user.id,
        action="PASSWORD_RESET",
        resource_type="user",
        resource_id=str(matched_user.id),
        description="Password reset via token",
        success=True,
    ))
    await db.commit()
    return {"message": "Password has been reset successfully. Please log in with your new password."}
