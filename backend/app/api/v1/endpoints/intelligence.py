"""ARGUS — Threat Intelligence endpoints."""

import re
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin
from app.core.database import get_db
from app.models.indicator import Indicator, IndicatorType
from app.models.threat_intel import ThreatIntelResult
from app.schemas.intelligence import (
    IndicatorLookupRequest, IndicatorResponse, IndicatorListResponse,
    ThreatIntelResultResponse,
)

router = APIRouter()

# ── Validation helpers ────────────────────────────────────────────────────────

def _normalize_indicator(value: str, itype: IndicatorType) -> str:
    v = value.strip()
    if itype in (IndicatorType.IPV4, IndicatorType.IPV6, IndicatorType.DOMAIN, IndicatorType.EMAIL):
        v = v.lower()
    elif itype in (IndicatorType.MD5, IndicatorType.SHA1, IndicatorType.SHA256):
        v = v.lower()
        if not re.match(r'^[0-9a-f]+$', v):
            raise ValueError(f"Invalid hash format for {itype}")
    elif itype == IndicatorType.IPV4:
        import ipaddress
        ipaddress.IPv4Address(v)
    elif itype == IndicatorType.IPV6:
        import ipaddress
        ipaddress.IPv6Address(v)
    return v


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("", response_model=IndicatorListResponse)
async def list_indicators(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    indicator_type: Optional[IndicatorType] = Query(None),
    is_malicious: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, max_length=255),
):
    conditions = []
    if indicator_type:
        conditions.append(Indicator.indicator_type == indicator_type)
    if is_malicious is not None:
        conditions.append(Indicator.is_malicious == is_malicious)
    if search:
        conditions.append(Indicator.value.ilike(f"%{search}%"))

    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(Indicator.id)).where(where)) or 0
    result = await db.execute(
        select(Indicator).where(where)
        .order_by(Indicator.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return IndicatorListResponse(
        items=[IndicatorResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/lookup", response_model=IndicatorResponse, status_code=status.HTTP_201_CREATED)
async def lookup_indicator(
    payload: IndicatorLookupRequest,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit an IOC for lookup. Saves to the indicator database.
    External enrichment (VirusTotal, AbuseIPDB) runs if configured.
    """
    try:
        normalized = _normalize_indicator(payload.value, payload.indicator_type)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Check if already exists
    existing_r = await db.execute(
        select(Indicator).where(
            and_(Indicator.value == normalized, Indicator.indicator_type == payload.indicator_type)
        )
    )
    indicator = existing_r.scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if indicator:
        indicator.last_seen_at = now
        if payload.analyst_notes:
            indicator.analyst_notes = payload.analyst_notes
        await db.commit()
        await db.refresh(indicator)
    else:
        indicator = Indicator(
            value=normalized,
            indicator_type=payload.indicator_type,
            analyst_notes=payload.analyst_notes,
            source="analyst-lookup",
            first_seen_at=now,
            last_seen_at=now,
            created_by_id=current_user.id,
        )
        db.add(indicator)
        await db.flush()
        await db.commit()
        await db.refresh(indicator)

    # ── Optional external enrichment ──────────────────────────────────────
    from app.core.config import settings
    provider_result = None

    if settings.virustotal_enabled and payload.indicator_type in (
        IndicatorType.IPV4, IndicatorType.IPV6, IndicatorType.DOMAIN,
        IndicatorType.URL, IndicatorType.MD5, IndicatorType.SHA256
    ):
        provider_result = await _query_virustotal(indicator, settings.VIRUSTOTAL_API_KEY, db, current_user.id)

    return IndicatorResponse.model_validate(indicator)


@router.get("/{indicator_id}", response_model=IndicatorResponse)
async def get_indicator(
    indicator_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Indicator).where(Indicator.id == indicator_id))
    ind = result.scalar_one_or_none()
    if not ind:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return IndicatorResponse.model_validate(ind)


@router.get("/{indicator_id}/results", response_model=list[ThreatIntelResultResponse])
async def get_indicator_results(
    indicator_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ThreatIntelResult)
        .where(ThreatIntelResult.indicator_id == indicator_id)
        .order_by(ThreatIntelResult.queried_at.desc())
    )
    return [ThreatIntelResultResponse.model_validate(r) for r in result.scalars().all()]


# ── External provider helpers ─────────────────────────────────────────────────

async def _query_virustotal(indicator: Indicator, api_key: str, db: AsyncSession, user_id) -> Optional[ThreatIntelResult]:
    """Query VirusTotal for the indicator. Returns a cached or fresh result."""
    import httpx
    from app.models.indicator import IndicatorType as IT

    # Map indicator type to VT endpoint
    itype = indicator.indicator_type
    if itype == IT.IPV4:
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{indicator.value}"
    elif itype == IT.DOMAIN:
        url = f"https://www.virustotal.com/api/v3/domains/{indicator.value}"
    elif itype in (IT.MD5, IT.SHA256, IT.SHA1):
        url = f"https://www.virustotal.com/api/v3/files/{indicator.value}"
    elif itype == IT.URL:
        import base64
        encoded = base64.urlsafe_b64encode(indicator.value.encode()).decode().rstrip("=")
        url = f"https://www.virustotal.com/api/v3/urls/{encoded}"
    else:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"x-apikey": api_key})

        if resp.status_code == 200:
            data = resp.json()
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            total_engines = sum(stats.values()) if stats else 0
            is_mal = malicious > 0
            score = int((malicious / total_engines * 100)) if total_engines > 0 else 0

            result = ThreatIntelResult(
                indicator_id=indicator.id,
                provider="virustotal",
                raw_response=data,
                is_malicious=is_mal,
                reputation_score=score,
                summary=f"{malicious}/{total_engines} engines flagged as malicious",
                is_cached=False,
                queried_by_id=user_id,
            )
            # Update indicator reputation
            indicator.is_malicious = is_mal
            indicator.reputation_score = score
        else:
            result = ThreatIntelResult(
                indicator_id=indicator.id,
                provider="virustotal",
                error_message=f"HTTP {resp.status_code}: {resp.text[:200]}",
                is_cached=False,
                queried_by_id=user_id,
            )
    except Exception as exc:
        result = ThreatIntelResult(
            indicator_id=indicator.id,
            provider="virustotal",
            error_message=f"Request failed: {str(exc)[:200]}",
            is_cached=False,
            queried_by_id=user_id,
        )

    db.add(result)
    await db.commit()
    return result
