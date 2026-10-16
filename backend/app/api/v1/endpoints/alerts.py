"""ARGUS — Alerts endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin
from app.core.database import get_db
from app.models.alert import Alert, AlertStatus
from app.schemas.alerts import AlertResponse, AlertUpdate, AlertListResponse

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_status: Optional[AlertStatus] = Query(None, alias="status"),
    severity: Optional[str] = Query(None),
):
    conditions = []
    if alert_status:
        conditions.append(Alert.status == alert_status)
    if severity:
        conditions.append(Alert.severity == severity.upper())

    from sqlalchemy import and_
    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(Alert.id)).where(where)) or 0
    result = await db.execute(
        select(Alert).where(where)
        .order_by(Alert.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return AlertListResponse(
        items=[AlertResponse.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertResponse.model_validate(alert)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert_status(
    alert_id: UUID,
    payload: AlertUpdate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = payload.status
    await db.commit()
    await db.refresh(alert)
    return AlertResponse.model_validate(alert)
