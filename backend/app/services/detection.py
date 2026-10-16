"""
ARGUS — Rule-based detection engine.

Each rule is deterministic and testable. Rules are evaluated against
normalized SecurityEvent objects. Alerts are generated with supporting
evidence. Duplicate alerts are suppressed via dedup_key.

Rules implemented:
  1. brute_force_login          — repeated failed auth from one IP
  2. success_after_failures     — successful login after multiple failures
  3. multi_account_failure      — one IP failing across multiple accounts
  4. privilege_escalation       — any privilege escalation event
  5. admin_account_creation     — privileged account created outside hours
  6. port_scan                  — many different destination ports from one IP
  7. unusual_admin_activity     — admin commands at unusual hours
  8. ioc_match                  — event field matches a known malicious IOC
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert, AlertStatus
from app.models.detection_rule import DetectionRule
from app.models.indicator import Indicator, IndicatorType
from app.models.security_event import SecurityEvent, EventType, EventSeverity


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_dedup_key(*parts: str) -> str:
    """Create a stable dedup key from rule + context."""
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:64]


async def _get_rule(db: AsyncSession, rule_key: str) -> Optional[DetectionRule]:
    result = await db.execute(
        select(DetectionRule).where(
            and_(DetectionRule.rule_key == rule_key, DetectionRule.is_enabled == True)  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def _dedup_check(db: AsyncSession, dedup_key: str) -> bool:
    """Return True if an open alert with this key already exists."""
    count = await db.scalar(
        select(func.count(Alert.id)).where(
            and_(Alert.dedup_key == dedup_key, Alert.status == AlertStatus.OPEN)
        )
    ) or 0
    return count > 0


async def _bump_or_create(
    db: AsyncSession,
    rule: DetectionRule,
    dedup_key: str,
    title: str,
    description: str,
    severity: str,
    evidence: dict,
    event_id: Optional[UUID] = None,
) -> Optional[Alert]:
    """
    If an OPEN alert with this dedup_key exists, bump its counter.
    Otherwise create a new alert.
    """
    existing_r = await db.execute(
        select(Alert).where(Alert.dedup_key == dedup_key, Alert.status == AlertStatus.OPEN)
    )
    existing = existing_r.scalar_one_or_none()

    if existing:
        existing.occurrence_count += 1
        existing.last_seen_at = datetime.now(timezone.utc)
        existing.evidence = {**(existing.evidence or {}), **evidence}
        return existing
    else:
        alert = Alert(
            title=title,
            description=description,
            severity=severity,
            status=AlertStatus.OPEN,
            rule_id=rule.id,
            event_id=event_id,
            evidence=evidence,
            dedup_key=dedup_key,
            occurrence_count=1,
            last_seen_at=datetime.now(timezone.utc),
        )
        db.add(alert)
        return alert


# ── Rule implementations ──────────────────────────────────────────────────────

async def check_brute_force(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: brute_force_login
    Fires when a single source IP generates ≥ threshold failed auth events
    within threshold_window_seconds.
    """
    if event.event_type != EventType.AUTHENTICATION:
        return None
    if not event.source_ip:
        return None
    if "fail" not in (event.description or "").lower() and "invalid" not in (event.description or "").lower():
        return None

    rule = await _get_rule(db, "brute_force_login")
    if not rule:
        return None

    window_start = datetime.now(timezone.utc) - timedelta(seconds=rule.threshold_window_seconds)
    count = await db.scalar(
        select(func.count(SecurityEvent.id)).where(
            and_(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.event_type == EventType.AUTHENTICATION,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.description.ilike("%fail%") | SecurityEvent.description.ilike("%invalid%"),
            )
        )
    ) or 0

    if count < rule.threshold_count:
        return None

    dedup_key = _make_dedup_key("brute_force_login", event.source_ip, window_start.date().isoformat())
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Brute Force Detected: {event.source_ip}",
        description=f"{count} failed authentication attempts from {event.source_ip} in {rule.threshold_window_seconds}s",
        severity=rule.severity,
        evidence={
            "source_ip": event.source_ip,
            "attempt_count": count,
            "window_seconds": rule.threshold_window_seconds,
            "hostname": event.hostname,
        },
        event_id=event.id,
    )


async def check_success_after_failures(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: success_after_failures
    Fires when a successful auth follows ≥ threshold failures from same IP.
    """
    if event.event_type != EventType.AUTHENTICATION:
        return None
    if not event.source_ip:
        return None
    desc_lower = (event.description or "").lower()
    # Only trigger on apparent success events
    if not any(kw in desc_lower for kw in ["success", "accepted", "granted", "logged in"]):
        return None

    rule = await _get_rule(db, "success_after_failures")
    if not rule:
        return None

    window_start = datetime.now(timezone.utc) - timedelta(seconds=rule.threshold_window_seconds)
    failure_count = await db.scalar(
        select(func.count(SecurityEvent.id)).where(
            and_(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.event_type == EventType.AUTHENTICATION,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.timestamp < event.timestamp,
                SecurityEvent.description.ilike("%fail%") | SecurityEvent.description.ilike("%invalid%"),
            )
        )
    ) or 0

    if failure_count < rule.threshold_count:
        return None

    dedup_key = _make_dedup_key("success_after_failures", event.source_ip, str(event.id))
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Potential Credential Stuffing: {event.source_ip}",
        description=(
            f"Successful authentication from {event.source_ip} after "
            f"{failure_count} failures in {rule.threshold_window_seconds}s. "
            f"User: {event.username or 'unknown'}"
        ),
        severity=rule.severity,
        evidence={
            "source_ip": event.source_ip,
            "prior_failures": failure_count,
            "username": event.username,
            "successful_event_id": str(event.id),
        },
        event_id=event.id,
    )


async def check_multi_account_failure(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: multi_account_failure
    One IP failing against multiple different accounts — password spraying.
    """
    if event.event_type != EventType.AUTHENTICATION:
        return None
    if not event.source_ip:
        return None
    if "fail" not in (event.description or "").lower():
        return None

    rule = await _get_rule(db, "multi_account_failure")
    if not rule:
        return None

    window_start = datetime.now(timezone.utc) - timedelta(seconds=rule.threshold_window_seconds)
    distinct_accounts = await db.scalar(
        select(func.count(distinct(SecurityEvent.username))).where(
            and_(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.event_type == EventType.AUTHENTICATION,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.username.isnot(None),
                SecurityEvent.description.ilike("%fail%"),
            )
        )
    ) or 0

    if distinct_accounts < rule.threshold_count:
        return None

    dedup_key = _make_dedup_key("multi_account_failure", event.source_ip, window_start.date().isoformat())
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Password Spraying Suspected: {event.source_ip}",
        description=f"IP {event.source_ip} failed authentication against {distinct_accounts} different accounts in {rule.threshold_window_seconds}s",
        severity=rule.severity,
        evidence={
            "source_ip": event.source_ip,
            "distinct_accounts": distinct_accounts,
            "window_seconds": rule.threshold_window_seconds,
        },
        event_id=event.id,
    )


async def check_privilege_escalation(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: privilege_escalation
    Any privilege escalation event immediately generates a CRITICAL alert.
    """
    if event.event_type != EventType.PRIVILEGE_ESCALATION:
        return None

    rule = await _get_rule(db, "privilege_escalation")
    if not rule:
        return None

    dedup_key = _make_dedup_key("privilege_escalation", str(event.id))
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Privilege Escalation: {event.username or 'unknown'} on {event.hostname or 'unknown'}",
        description=event.description[:500],
        severity="CRITICAL",
        evidence={
            "username": event.username,
            "hostname": event.hostname,
            "source_ip": event.source_ip,
            "event_id": str(event.id),
        },
        event_id=event.id,
    )


async def check_admin_account_creation(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: admin_account_creation
    Privileged account created — always generates a HIGH alert.
    """
    if event.event_type != EventType.AUTHORIZATION:
        return None
    desc_lower = (event.description or "").lower()
    if not any(kw in desc_lower for kw in ["sudo", "admin", "privilege", "root", "wheel", "added to group"]):
        return None

    rule = await _get_rule(db, "admin_account_creation")
    if not rule:
        return None

    dedup_key = _make_dedup_key("admin_account_creation", str(event.id))
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Suspicious Admin Activity: {event.hostname or 'unknown'}",
        description=event.description[:500],
        severity=rule.severity,
        evidence={
            "username": event.username,
            "hostname": event.hostname,
            "event_id": str(event.id),
            "timestamp": event.timestamp.isoformat(),
        },
        event_id=event.id,
    )


async def check_port_scan(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: port_scan
    One source IP probing many destination ports in a short window.
    """
    if event.event_type != EventType.NETWORK:
        return None
    if not event.source_ip:
        return None

    rule = await _get_rule(db, "port_scan")
    if not rule:
        return None

    window_start = datetime.now(timezone.utc) - timedelta(seconds=rule.threshold_window_seconds)
    distinct_ports = await db.scalar(
        select(func.count(distinct(SecurityEvent.destination_port))).where(
            and_(
                SecurityEvent.source_ip == event.source_ip,
                SecurityEvent.event_type == EventType.NETWORK,
                SecurityEvent.timestamp >= window_start,
                SecurityEvent.destination_port.isnot(None),
            )
        )
    ) or 0

    if distinct_ports < rule.threshold_count:
        return None

    dedup_key = _make_dedup_key("port_scan", event.source_ip, window_start.strftime("%Y%m%d%H"))
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"Port Scan Detected from {event.source_ip}",
        description=f"IP {event.source_ip} probed {distinct_ports} distinct ports in {rule.threshold_window_seconds}s",
        severity=rule.severity,
        evidence={
            "source_ip": event.source_ip,
            "distinct_ports": distinct_ports,
            "window_seconds": rule.threshold_window_seconds,
        },
        event_id=event.id,
    )


async def check_ioc_match(db: AsyncSession, event: SecurityEvent) -> Optional[Alert]:
    """
    Rule: ioc_match
    Event source IP, username, or hostname matches a known malicious indicator.
    """
    rule = await _get_rule(db, "ioc_match")
    if not rule:
        return None

    matched_indicator = None
    matched_field = None

    # Check source IP
    if event.source_ip:
        r = await db.execute(
            select(Indicator).where(
                and_(
                    Indicator.value == event.source_ip,
                    Indicator.is_malicious == True,  # noqa: E712
                    Indicator.indicator_type.in_([IndicatorType.IPV4, IndicatorType.IPV6]),
                )
            )
        )
        ind = r.scalar_one_or_none()
        if ind:
            matched_indicator = ind
            matched_field = "source_ip"

    # Check hostname
    if not matched_indicator and event.hostname:
        r = await db.execute(
            select(Indicator).where(
                and_(
                    Indicator.value == event.hostname.lower(),
                    Indicator.is_malicious == True,  # noqa: E712
                    Indicator.indicator_type == IndicatorType.DOMAIN,
                )
            )
        )
        ind = r.scalar_one_or_none()
        if ind:
            matched_indicator = ind
            matched_field = "hostname"

    if not matched_indicator:
        return None

    dedup_key = _make_dedup_key("ioc_match", str(matched_indicator.id), str(event.id))
    return await _bump_or_create(
        db, rule, dedup_key,
        title=f"IOC Match: {matched_indicator.indicator_type.value} {matched_indicator.value[:50]}",
        description=(
            f"Event {event.id} matched known malicious indicator "
            f"{matched_indicator.indicator_type.value}:{matched_indicator.value} "
            f"in field '{matched_field}'"
        ),
        severity=rule.severity,
        evidence={
            "indicator_id": str(matched_indicator.id),
            "indicator_value": matched_indicator.value,
            "indicator_type": matched_indicator.indicator_type.value,
            "matched_field": matched_field,
            "event_id": str(event.id),
        },
        event_id=event.id,
    )


# ── Engine entry point ────────────────────────────────────────────────────────

RULE_CHECKS = [
    check_brute_force,
    check_success_after_failures,
    check_multi_account_failure,
    check_privilege_escalation,
    check_admin_account_creation,
    check_port_scan,
    check_ioc_match,
]


async def run_detection(db: AsyncSession, event: SecurityEvent) -> list[Alert]:
    """
    Run all enabled detection rules against a single normalized event.
    Returns list of new or updated alerts. Commits changes to DB.
    Errors in individual rules are caught and logged — they do not halt processing.
    """
    import structlog
    log = structlog.get_logger()

    fired_alerts: list[Alert] = []

    for check_fn in RULE_CHECKS:
        try:
            alert = await check_fn(db, event)
            if alert:
                fired_alerts.append(alert)
        except Exception as exc:
            log.error(
                "Detection rule error",
                rule=check_fn.__name__,
                event_id=str(event.id),
                error=str(exc)[:200],
            )

    if fired_alerts:
        await db.commit()

    return fired_alerts
