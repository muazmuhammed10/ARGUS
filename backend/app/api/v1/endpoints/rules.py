"""ARGUS — Detection rules endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AdminUser
from app.core.database import get_db
from app.models.detection_rule import DetectionRule
from app.models.audit_log import AuditLog
from app.schemas.rules import RuleUpdate, RuleResponse, RuleListResponse

router = APIRouter()


@router.get("", response_model=RuleListResponse)
async def list_rules(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    enabled_only: bool = Query(False),
):
    conditions = []
    if enabled_only:
        conditions.append(DetectionRule.is_enabled == True)  # noqa: E712

    from sqlalchemy import and_
    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(DetectionRule.id)).where(where)) or 0
    result = await db.execute(
        select(DetectionRule).where(where).order_by(DetectionRule.name.asc())
    )
    rules = result.scalars().all()
    return RuleListResponse(
        items=[RuleResponse.model_validate(r) for r in rules],
        total=total,
    )


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
):
    """Admin-only: update a detection rule's configuration."""
    result = await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Detection rule not found")

    changes = []
    for field, val in payload.model_dump(exclude_unset=True).items():
        old = getattr(rule, field)
        if old != val:
            setattr(rule, field, val)
            changes.append(f"{field}: {old} → {val}")

    if changes:
        db.add(AuditLog(
            user_id=current_user.id,
            action="RULE_UPDATED",
            resource_type="detection_rule",
            resource_id=str(rule.id),
            description=f"Rule '{rule.name}' updated: {'; '.join(changes)}",
            success=True,
        ))

    await db.commit()
    await db.refresh(rule)
    return RuleResponse.model_validate(rule)


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(DetectionRule).where(DetectionRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Detection rule not found")
    return RuleResponse.model_validate(rule)
