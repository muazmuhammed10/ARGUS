"""
ARGUS — Report export endpoints.
GET  /reports                     list available report types
POST /reports/export              generate and export a report
"""

import csv
import html
import io
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin
from app.core.database import get_db
from app.models.security_event import SecurityEvent, EventSeverity
from app.models.incident import Incident
from app.models.detection_rule import DetectionRule
from app.models.asset import Asset
from app.models.alert import Alert
from app.models.indicator import Indicator

router = APIRouter()

REPORT_TYPES = [
    {"id": "security_events", "title": "Security Event Summary", "formats": ["csv", "json", "html"]},
    {"id": "incidents", "title": "Incident Investigation Report", "formats": ["json", "html"]},
    {"id": "threat_intelligence", "title": "Threat Intelligence Report", "formats": ["csv", "json"]},
    {"id": "detection_rules", "title": "Detection Rule Activity", "formats": ["csv", "html"]},
    {"id": "assets", "title": "Asset Security Overview", "formats": ["csv", "json", "html"]},
]


@router.get("")
async def list_reports(current_user: AnyRole):
    return {"items": REPORT_TYPES, "total": len(REPORT_TYPES)}


def _escape_csv_cell(value: str) -> str:
    """Prevent CSV formula injection by prefixing dangerous characters."""
    v = str(value) if value is not None else ""
    if v and v[0] in ("=", "+", "-", "@", "\t", "\r"):
        v = "'" + v
    return v


def _html_report_wrapper(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ARGUS — {html.escape(title)}</title>
  <style>
    body {{ font-family: Inter, sans-serif; background: #0d1420; color: #e5e7eb; margin: 2rem; }}
    h1 {{ color: #00d4ff; }} h2 {{ color: #9ca3af; border-bottom: 1px solid #374151; padding-bottom: .5rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th {{ background: #1e2535; color: #00d4ff; padding: .5rem 1rem; text-align: left; font-size: .8rem; text-transform: uppercase; }}
    td {{ border-bottom: 1px solid #1e2535; padding: .5rem 1rem; font-size: .85rem; }}
    tr:hover td {{ background: #162338; }}
    .badge-critical {{ color: #ef4444; }} .badge-high {{ color: #f97316; }}
    .badge-medium {{ color: #eab308; }} .badge-low {{ color: #22c55e; }}
    .footer {{ margin-top: 2rem; color: #6b7280; font-size: .75rem; }}
  </style>
</head>
<body>
  <h1>ARGUS — {html.escape(title)}</h1>
  <p>Generated: {html.escape(datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))}</p>
  {body}
  <div class="footer">ARGUS Cyber Defense Platform — Report generated automatically. Do not distribute externally without review.</div>
</body>
</html>"""


@router.post("/export")
async def export_report(
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
    report_type: str = Query(...),
    fmt: str = Query("json", pattern="^(csv|json|html)$"),
    days: int = Query(30, ge=1, le=365),
):
    """Generate and download a security report."""
    valid_ids = {r["id"] for r in REPORT_TYPES}
    if report_type not in valid_ids:
        raise HTTPException(status_code=400, detail=f"Unknown report type: {report_type}")

    since = datetime.now(timezone.utc) - timedelta(days=days)

    if report_type == "security_events":
        return await _export_events(db, fmt, since, days)
    elif report_type == "incidents":
        return await _export_incidents(db, fmt, since)
    elif report_type == "threat_intelligence":
        return await _export_intel(db, fmt)
    elif report_type == "detection_rules":
        return await _export_rules(db, fmt)
    elif report_type == "assets":
        return await _export_assets(db, fmt)
    else:
        raise HTTPException(status_code=400, detail="Report not implemented")


async def _export_events(db: AsyncSession, fmt: str, since: datetime, days: int):
    result = await db.execute(
        select(SecurityEvent).where(SecurityEvent.timestamp >= since)
        .order_by(SecurityEvent.timestamp.desc()).limit(5000)
    )
    events = result.scalars().all()

    if fmt == "csv":
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["Timestamp", "Severity", "EventType", "SourceSystem", "SourceIP", "Username", "Hostname", "Description"])
        for e in events:
            w.writerow([
                _escape_csv_cell(str(e.timestamp)),
                _escape_csv_cell(e.severity.value),
                _escape_csv_cell(e.event_type.value),
                _escape_csv_cell(e.source_system),
                _escape_csv_cell(e.source_ip or ""),
                _escape_csv_cell(e.username or ""),
                _escape_csv_cell(e.hostname or ""),
                _escape_csv_cell(e.description[:200]),
            ])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=argus_events_{days}d.csv"},
        )

    elif fmt == "json":
        data = [{
            "id": str(e.id), "timestamp": e.timestamp.isoformat(),
            "severity": e.severity.value, "event_type": e.event_type.value,
            "source_system": e.source_system, "source_ip": e.source_ip,
            "username": e.username, "hostname": e.hostname,
            "description": e.description, "is_synthetic": e.is_synthetic,
        } for e in events]
        return JSONResponse({"report_type": "security_events", "days": days, "count": len(data), "items": data})

    else:  # html
        rows = "".join(
            f"<tr><td>{html.escape(str(e.timestamp)[:19])}</td>"
            f"<td class='badge-{e.severity.value.lower()}'>{html.escape(e.severity.value)}</td>"
            f"<td>{html.escape(e.event_type.value)}</td>"
            f"<td>{html.escape(e.source_ip or '')}</td>"
            f"<td>{html.escape(e.username or '')}</td>"
            f"<td>{html.escape(e.description[:100])}</td></tr>"
            for e in events
        )
        body = f"<h2>Security Events — Last {days} Days ({len(events)} records)</h2>"
        body += "<table><thead><tr><th>Timestamp</th><th>Severity</th><th>Type</th><th>Source IP</th><th>User</th><th>Description</th></tr></thead>"
        body += f"<tbody>{rows}</tbody></table>"
        return StreamingResponse(
            iter([_html_report_wrapper("Security Event Summary", body)]),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=argus_events.html"},
        )


async def _export_incidents(db: AsyncSession, fmt: str, since: datetime):
    result = await db.execute(
        select(Incident).where(Incident.created_at >= since)
        .order_by(Incident.created_at.desc()).limit(1000)
    )
    incidents = result.scalars().all()

    if fmt == "json":
        data = [{
            "id": str(i.id), "title": i.title, "severity": i.severity.value,
            "status": i.status.value, "created_at": i.created_at.isoformat(),
            "updated_at": i.updated_at.isoformat(),
        } for i in incidents]
        return JSONResponse({"report_type": "incidents", "count": len(data), "items": data})
    else:
        rows = "".join(
            f"<tr><td>{html.escape(i.title)}</td>"
            f"<td>{html.escape(i.severity.value)}</td>"
            f"<td>{html.escape(i.status.value)}</td>"
            f"<td>{html.escape(str(i.created_at)[:19])}</td></tr>"
            for i in incidents
        )
        body = f"<h2>Incidents ({len(incidents)} records)</h2>"
        body += "<table><thead><tr><th>Title</th><th>Severity</th><th>Status</th><th>Created</th></tr></thead>"
        body += f"<tbody>{rows}</tbody></table>"
        return StreamingResponse(
            iter([_html_report_wrapper("Incident Investigation Report", body)]),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=argus_incidents.html"},
        )


async def _export_intel(db: AsyncSession, fmt: str):
    result = await db.execute(
        select(Indicator).order_by(Indicator.created_at.desc()).limit(2000)
    )
    indicators = result.scalars().all()

    if fmt == "csv":
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["Type", "Value", "Malicious", "Confidence", "Source", "FirstSeen", "LastSeen"])
        for ind in indicators:
            w.writerow([
                _escape_csv_cell(ind.indicator_type.value),
                _escape_csv_cell(ind.value),
                _escape_csv_cell(str(ind.is_malicious) if ind.is_malicious is not None else "unknown"),
                _escape_csv_cell(str(ind.confidence or "")),
                _escape_csv_cell(ind.source or ""),
                _escape_csv_cell(str(ind.first_seen_at)[:19] if ind.first_seen_at else ""),
                _escape_csv_cell(str(ind.last_seen_at)[:19] if ind.last_seen_at else ""),
            ])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=argus_intel.csv"},
        )
    else:
        data = [{
            "type": ind.indicator_type.value, "value": ind.value,
            "is_malicious": ind.is_malicious, "confidence": ind.confidence,
            "source": ind.source,
        } for ind in indicators]
        return JSONResponse({"report_type": "threat_intelligence", "count": len(data), "items": data})


async def _export_rules(db: AsyncSession, fmt: str):
    result = await db.execute(select(DetectionRule).order_by(DetectionRule.name))
    rules = result.scalars().all()

    if fmt == "csv":
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["Name", "Category", "Severity", "Enabled", "Threshold", "WindowSec", "RuleKey"])
        for r in rules:
            w.writerow([
                _escape_csv_cell(r.name), _escape_csv_cell(r.category.value),
                _escape_csv_cell(r.severity), _escape_csv_cell(str(r.is_enabled)),
                _escape_csv_cell(str(r.threshold_count)), _escape_csv_cell(str(r.threshold_window_seconds)),
                _escape_csv_cell(r.rule_key),
            ])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=argus_rules.csv"},
        )
    else:
        rows = "".join(
            f"<tr><td>{html.escape(r.name)}</td><td>{html.escape(r.category.value)}</td>"
            f"<td>{html.escape(r.severity)}</td><td>{'✅' if r.is_enabled else '❌'}</td>"
            f"<td>{r.threshold_count}/{r.threshold_window_seconds}s</td></tr>"
            for r in rules
        )
        body = "<h2>Detection Rules</h2><table><thead><tr><th>Name</th><th>Category</th><th>Severity</th><th>Enabled</th><th>Threshold</th></tr></thead>"
        body += f"<tbody>{rows}</tbody></table>"
        return StreamingResponse(
            iter([_html_report_wrapper("Detection Rule Activity", body)]),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=argus_rules.html"},
        )


async def _export_assets(db: AsyncSession, fmt: str):
    result = await db.execute(select(Asset).order_by(Asset.name))
    assets = result.scalars().all()

    if fmt == "csv":
        output = io.StringIO()
        w = csv.writer(output)
        w.writerow(["Name", "Hostname", "IP", "OS", "Environment", "Criticality", "Owner", "Status"])
        for a in assets:
            w.writerow([
                _escape_csv_cell(a.name), _escape_csv_cell(a.hostname or ""),
                _escape_csv_cell(a.ip_address or ""), _escape_csv_cell(a.operating_system or ""),
                _escape_csv_cell(a.environment.value), _escape_csv_cell(a.criticality.value),
                _escape_csv_cell(a.owner or ""), _escape_csv_cell(a.monitoring_status),
            ])
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=argus_assets.csv"},
        )
    elif fmt == "json":
        data = [{
            "name": a.name, "hostname": a.hostname, "ip_address": a.ip_address,
            "environment": a.environment.value, "criticality": a.criticality.value,
            "owner": a.owner, "monitoring_status": a.monitoring_status,
        } for a in assets]
        return JSONResponse({"report_type": "assets", "count": len(data), "items": data})
    else:
        rows = "".join(
            f"<tr><td>{html.escape(a.name)}</td><td>{html.escape(a.hostname or '')}</td>"
            f"<td>{html.escape(a.ip_address or '')}</td><td>{html.escape(a.environment.value)}</td>"
            f"<td>{html.escape(a.criticality.value)}</td><td>{html.escape(a.owner or '')}</td></tr>"
            for a in assets
        )
        body = "<h2>Asset Inventory</h2><table><thead><tr><th>Name</th><th>Hostname</th><th>IP</th><th>Environment</th><th>Criticality</th><th>Owner</th></tr></thead>"
        body += f"<tbody>{rows}</tbody></table>"
        return StreamingResponse(
            iter([_html_report_wrapper("Asset Security Overview", body)]),
            media_type="text/html",
            headers={"Content-Disposition": "attachment; filename=argus_assets.html"},
        )
