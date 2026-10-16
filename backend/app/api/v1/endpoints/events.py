"""
ARGUS — Security Events endpoints.
GET    /events              list with filters + pagination
GET    /events/{id}         single event detail
POST   /events/ingest       single-event API ingestion
POST   /events/import       JSON Lines file import
PATCH  /events/{id}         update detection status
"""

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin, CurrentUser
from app.core.database import get_db
from app.models.security_event import (
    SecurityEvent, EventSeverity, EventType, DetectionStatus
)
from app.schemas.events import (
    EventIngestRequest, EventResponse, EventListResponse
)

router = APIRouter()
_MAX_IMPORT_BYTES = 10 * 1024 * 1024   # 10 MB


def _dedup_hash(event: SecurityEvent) -> str:
    """Produce a deduplication hash from stable event fields."""
    parts = "|".join([
        str(event.timestamp.isoformat() if event.timestamp else ""),
        event.source_system or "",
        event.event_type.value if event.event_type else "",
        event.source_ip or "",
        event.destination_ip or "",
        str(event.source_port or ""),
        str(event.destination_port or ""),
        event.username or "",
        event.hostname or "",
    ])
    return hashlib.sha256(parts.encode()).hexdigest()[:64]


def _build_event(payload: EventIngestRequest) -> SecurityEvent:
    ts = payload.timestamp or datetime.now(timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    ev = SecurityEvent(
        timestamp=ts,
        source_system=payload.source_system,
        event_type=payload.event_type,
        severity=payload.severity,
        source_ip=payload.source_ip,
        destination_ip=payload.destination_ip,
        source_port=payload.source_port,
        destination_port=payload.destination_port,
        username=payload.username,
        hostname=payload.hostname,
        description=payload.description[:10000],   # guard length
        metadata_json=payload.metadata_json,
        is_synthetic=payload.is_synthetic,
        detection_status=DetectionStatus.UNREVIEWED,
    )
    ev.dedup_hash = _dedup_hash(ev)
    return ev


# ─────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=EventListResponse)
async def list_events(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    severity: Optional[EventSeverity] = Query(None),
    event_type: Optional[EventType] = Query(None),
    detection_status: Optional[DetectionStatus] = Query(None),
    source_ip: Optional[str] = Query(None, max_length=45),
    username: Optional[str] = Query(None, max_length=255),
    hostname: Optional[str] = Query(None, max_length=255),
    is_synthetic: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=255),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
):
    """List security events with filters and pagination."""
    conditions = []
    if severity:
        conditions.append(SecurityEvent.severity == severity)
    if event_type:
        conditions.append(SecurityEvent.event_type == event_type)
    if detection_status:
        conditions.append(SecurityEvent.detection_status == detection_status)
    if source_ip:
        conditions.append(SecurityEvent.source_ip == source_ip)
    if username:
        conditions.append(SecurityEvent.username.ilike(f"%{username}%"))
    if hostname:
        conditions.append(SecurityEvent.hostname.ilike(f"%{hostname}%"))
    if is_synthetic is not None:
        conditions.append(SecurityEvent.is_synthetic == is_synthetic)
    if search:
        conditions.append(
            or_(
                SecurityEvent.description.ilike(f"%{search}%"),
                SecurityEvent.source_ip.ilike(f"%{search}%"),
                SecurityEvent.username.ilike(f"%{search}%"),
                SecurityEvent.hostname.ilike(f"%{search}%"),
                SecurityEvent.source_system.ilike(f"%{search}%"),
            )
        )
    if from_date:
        conditions.append(SecurityEvent.timestamp >= from_date)
    if to_date:
        conditions.append(SecurityEvent.timestamp <= to_date)

    where = and_(*conditions) if conditions else True

    total = await db.scalar(select(func.count(SecurityEvent.id)).where(where)) or 0
    result = await db.execute(
        select(SecurityEvent)
        .where(where)
        .order_by(SecurityEvent.timestamp.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    events = result.scalars().all()
    return EventListResponse(
        items=[EventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single security event by ID."""
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse.model_validate(ev)


@router.post("/ingest", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def ingest_event(
    payload: EventIngestRequest,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single normalized security event via the API."""
    ev = _build_event(payload)

    # Deduplication check
    existing = await db.scalar(
        select(SecurityEvent.id).where(SecurityEvent.dedup_hash == ev.dedup_hash)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Duplicate event — already ingested")

    db.add(ev)
    await db.flush()

    # Run detection engine on the new event
    try:
        from app.services.detection import run_detection
        await run_detection(db, ev)
    except Exception:
        pass  # Detection errors never block ingestion

    await db.commit()
    await db.refresh(ev)
    return EventResponse.model_validate(ev)


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_events(
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """
    Import events from a JSON Lines (.jsonl) file.
    Each line must be a valid JSON object matching EventIngestRequest.
    Maximum file size: 10 MB.
    File contents are parsed and validated — never executed.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("jsonl", "json", "txt"):
        raise HTTPException(status_code=400, detail="Only .jsonl, .json, or .txt files are accepted")

    raw = await file.read(_MAX_IMPORT_BYTES + 1)
    if len(raw) > _MAX_IMPORT_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    lines = raw.decode("utf-8", errors="replace").splitlines()
    ingested, skipped, errors = 0, 0, []

    for line_no, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            payload = EventIngestRequest.model_validate(data)
            ev = _build_event(payload)
            existing = await db.scalar(
                select(SecurityEvent.id).where(SecurityEvent.dedup_hash == ev.dedup_hash)
            )
            if existing:
                skipped += 1
                continue
            db.add(ev)
            ingested += 1
        except Exception as exc:
            errors.append({"line": line_no, "error": str(exc)[:200]})
            if len(errors) >= 50:
                errors.append({"line": -1, "error": "Too many errors — truncated"})
                break

    if ingested:
        await db.commit()

    return {
        "ingested": ingested,
        "skipped_duplicates": skipped,
        "errors": errors,
        "total_lines": len(lines),
    }


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event_status(
    event_id: UUID,
    detection_status: DetectionStatus,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    """Update the detection status of a security event."""
    result = await db.execute(select(SecurityEvent).where(SecurityEvent.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    ev.detection_status = detection_status
    await db.commit()
    await db.refresh(ev)
    return EventResponse.model_validate(ev)
