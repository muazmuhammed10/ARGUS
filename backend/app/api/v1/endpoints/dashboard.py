"""
ARGUS — Dashboard endpoints — real database queries.
GET /dashboard/summary   high-level metrics
GET /dashboard/trends    event counts over last 7 days
GET /dashboard/alerts    recent open alerts
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, distinct, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole
from app.core.database import get_db
from app.models.security_event import SecurityEvent, EventSeverity, EventType
from app.models.incident import Incident, IncidentStatus
from app.models.alert import Alert, AlertStatus
from app.models.asset import Asset
from app.models.investigation import Investigation, InvestigationStatus

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=90, description="Look-back window in days"),
):
    """Real-database dashboard summary."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_events = await db.scalar(select(func.count(SecurityEvent.id))) or 0
    recent_events = await db.scalar(
        select(func.count(SecurityEvent.id)).where(SecurityEvent.timestamp >= since)
    ) or 0

    critical_events = await db.scalar(
        select(func.count(SecurityEvent.id)).where(
            and_(SecurityEvent.severity == EventSeverity.CRITICAL,
                 SecurityEvent.timestamp >= since)
        )
    ) or 0
    high_events = await db.scalar(
        select(func.count(SecurityEvent.id)).where(
            and_(SecurityEvent.severity == EventSeverity.HIGH,
                 SecurityEvent.timestamp >= since)
        )
    ) or 0

    open_incidents = await db.scalar(
        select(func.count(Incident.id)).where(
            Incident.status.in_([
                IncidentStatus.NEW, IncidentStatus.TRIAGED, IncidentStatus.INVESTIGATING
            ])
        )
    ) or 0
    resolved_incidents = await db.scalar(
        select(func.count(Incident.id)).where(
            Incident.status.in_([IncidentStatus.RESOLVED, IncidentStatus.CLOSED])
        )
    ) or 0

    open_alerts = await db.scalar(
        select(func.count(Alert.id)).where(Alert.status == AlertStatus.OPEN)
    ) or 0

    unique_source_ips = await db.scalar(
        select(func.count(distinct(SecurityEvent.source_ip))).where(
            and_(SecurityEvent.source_ip.isnot(None), SecurityEvent.timestamp >= since)
        )
    ) or 0

    # Auth failures in window
    auth_failures = await db.scalar(
        select(func.count(SecurityEvent.id)).where(
            and_(
                SecurityEvent.event_type == EventType.AUTHENTICATION,
                SecurityEvent.description.ilike("%fail%"),
                SecurityEvent.timestamp >= since,
            )
        )
    ) or 0

    active_investigations = await db.scalar(
        select(func.count(Investigation.id)).where(
            Investigation.status.in_([
                InvestigationStatus.OPEN, InvestigationStatus.IN_PROGRESS
            ])
        )
    ) or 0

    total_assets = await db.scalar(select(func.count(Asset.id))) or 0

    return {
        "total_events": total_events,
        "recent_events": recent_events,
        "critical_events": critical_events,
        "high_events": high_events,
        "open_incidents": open_incidents,
        "resolved_incidents": resolved_incidents,
        "open_alerts": open_alerts,
        "unique_source_ips": unique_source_ips,
        "auth_failures": auth_failures,
        "active_investigations": active_investigations,
        "total_assets": total_assets,
        "window_days": days,
    }


@router.get("/trends")
async def get_dashboard_trends(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    days: int = Query(7, ge=1, le=30),
):
    """Event counts grouped by day and severity for the last N days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # Build per-day counts for each severity
    results = await db.execute(
        select(
            func.date_trunc("day", SecurityEvent.timestamp).label("day"),
            SecurityEvent.severity.label("severity"),
            func.count(SecurityEvent.id).label("count"),
        )
        .where(SecurityEvent.timestamp >= since)
        .group_by(text("day"), SecurityEvent.severity)
        .order_by(text("day"))
    )

    rows = results.all()

    # Pivot into day → severity counts
    day_map: dict = {}
    for row in rows:
        day_str = row.day.strftime("%Y-%m-%d") if row.day else "unknown"
        if day_str not in day_map:
            day_map[day_str] = {"day": day_str, "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        sev = row.severity.value.lower() if hasattr(row.severity, "value") else str(row.severity).lower()
        if sev in day_map[day_str]:
            day_map[day_str][sev] = row.count

    trend_data = sorted(day_map.values(), key=lambda x: x["day"])

    # Event type distribution
    type_results = await db.execute(
        select(
            SecurityEvent.event_type.label("event_type"),
            func.count(SecurityEvent.id).label("count"),
        )
        .where(SecurityEvent.timestamp >= since)
        .group_by(SecurityEvent.event_type)
        .order_by(func.count(SecurityEvent.id).desc())
    )
    event_types = [
        {"type": r.event_type.value if hasattr(r.event_type, "value") else r.event_type, "count": r.count}
        for r in type_results.all()
    ]

    return {
        "trend_data": trend_data,
        "event_type_distribution": event_types,
        "window_days": days,
    }


@router.get("/alerts/recent")
async def get_recent_alerts(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, ge=1, le=50),
):
    """Most recent open or acknowledged alerts."""
    result = await db.execute(
        select(Alert)
        .where(Alert.status.in_([AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED]))
        .order_by(Alert.created_at.desc())
        .limit(limit)
    )
    alerts = result.scalars().all()
    from app.schemas.alerts import AlertResponse
    return {"items": [AlertResponse.model_validate(a) for a in alerts], "total": len(alerts)}
