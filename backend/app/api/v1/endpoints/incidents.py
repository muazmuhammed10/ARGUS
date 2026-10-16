"""
ARGUS — Incident management endpoints.
GET    /incidents              list
POST   /incidents              create
GET    /incidents/{id}         detail
PATCH  /incidents/{id}         update
POST   /incidents/{id}/events  link event
POST   /incidents/{id}/alerts  create from alert
DELETE /incidents/{id}/events/{event_id}  unlink event
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin, CurrentUser
from app.core.database import get_db
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.incident_event import IncidentEvent
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.schemas.incidents import (
    IncidentCreate, IncidentUpdate, IncidentResponse, IncidentListResponse
)

router = APIRouter()


async def _write_audit(db, action: str, user_id, resource_id, description: str, ip: str = "api"):
    db.add(AuditLog(
        user_id=user_id, action=action, resource_type="incident",
        resource_id=str(resource_id), description=description, ip_address=ip, success=True,
    ))


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[IncidentSeverity] = Query(None),
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, max_length=255),
    assigned_to_me: bool = Query(False),
):
    conditions = []
    if severity:
        conditions.append(Incident.severity == severity)
    if status_filter:
        conditions.append(Incident.status == status_filter)
    if search:
        conditions.append(or_(
            Incident.title.ilike(f"%{search}%"),
            Incident.description.ilike(f"%{search}%"),
        ))
    if assigned_to_me:
        conditions.append(Incident.assigned_to_id == current_user.id)

    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(Incident.id)).where(where)) or 0
    result = await db.execute(
        select(Incident).where(where)
        .order_by(Incident.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return IncidentListResponse(
        items=[IncidentResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    payload: IncidentCreate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    inc = Incident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        status=IncidentStatus.NEW,
        assigned_to_id=payload.assigned_to_id,
        created_by_id=current_user.id,
    )
    db.add(inc)
    await db.flush()
    await _write_audit(db, "INCIDENT_CREATED", current_user.id, inc.id, f"Created: {inc.title}")
    await db.commit()
    await db.refresh(inc)
    return IncidentResponse.model_validate(inc)


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return IncidentResponse.model_validate(inc)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    inc = result.scalar_one_or_none()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    changes = []
    for field, val in payload.model_dump(exclude_unset=True).items():
        old = getattr(inc, field)
        if old != val:
            setattr(inc, field, val)
            changes.append(f"{field}: {old} → {val}")

    # Auto-set resolved_at / closed_at timestamps
    if payload.status == IncidentStatus.RESOLVED and not inc.resolved_at:
        inc.resolved_at = datetime.now(timezone.utc)
    if payload.status == IncidentStatus.CLOSED and not inc.closed_at:
        inc.closed_at = datetime.now(timezone.utc)

    if changes:
        await _write_audit(
            db, "INCIDENT_UPDATED", current_user.id, inc.id,
            f"Updated: {'; '.join(changes)}"
        )
    await db.commit()
    await db.refresh(inc)
    return IncidentResponse.model_validate(inc)


@router.post("/{incident_id}/events/{event_id}", status_code=status.HTTP_201_CREATED)
async def link_event(
    incident_id: UUID,
    event_id: UUID,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
    note: Optional[str] = Query(None, max_length=2000),
):
    """Link a security event to an incident."""
    # Verify both exist
    inc_r = await db.execute(select(Incident.id).where(Incident.id == incident_id))
    if not inc_r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Incident not found")

    ev_r = await db.execute(select(SecurityEvent.id).where(SecurityEvent.id == event_id))
    if not ev_r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Event not found")

    # Check not already linked
    existing = await db.scalar(
        select(func.count(IncidentEvent.id)).where(
            and_(IncidentEvent.incident_id == incident_id, IncidentEvent.event_id == event_id)
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Event already linked to this incident")

    ie = IncidentEvent(
        incident_id=incident_id,
        event_id=event_id,
        analyst_note=note,
        added_by_id=current_user.id,
    )
    db.add(ie)
    await db.commit()
    return {"message": "Event linked", "incident_id": str(incident_id), "event_id": str(event_id)}


@router.get("/{incident_id}/events")
async def get_incident_events(
    incident_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    """Get all events linked to an incident."""
    result = await db.execute(
        select(SecurityEvent)
        .join(IncidentEvent, IncidentEvent.event_id == SecurityEvent.id)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(SecurityEvent.timestamp.desc())
    )
    events = result.scalars().all()
    from app.schemas.events import EventResponse
    return {"items": [EventResponse.model_validate(e) for e in events], "total": len(events)}
