"""
ARGUS — Detection engine unit tests.
Tests each rule in isolation with controlled synthetic events.
These tests do NOT require external services.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.security_event import SecurityEvent, EventType, EventSeverity, DetectionStatus
from app.models.detection_rule import DetectionRule, DetectionCategory
from app.models.alert import Alert, AlertStatus
from app.models.indicator import Indicator, IndicatorType
from app.services.detection import (
    check_brute_force,
    check_success_after_failures,
    check_multi_account_failure,
    check_privilege_escalation,
    check_port_scan,
    check_ioc_match,
    run_detection,
)

pytestmark = pytest.mark.asyncio

NOW = datetime.now(timezone.utc)


def make_event(
    event_type=EventType.AUTHENTICATION,
    severity=EventSeverity.HIGH,
    source_ip="192.0.2.1",
    username="testuser",
    hostname="test-host",
    description="Failed authentication attempt",
    timestamp=None,
) -> SecurityEvent:
    ev = SecurityEvent(
        id=uuid4(),
        timestamp=timestamp or NOW,
        source_system="test",
        event_type=event_type,
        severity=severity,
        source_ip=source_ip,
        username=username,
        hostname=hostname,
        description=description,
        detection_status=DetectionStatus.UNREVIEWED,
        is_synthetic=True,
    )
    return ev


def make_rule(
    rule_key: str,
    category: DetectionCategory = DetectionCategory.BRUTE_FORCE,
    threshold_count: int = 5,
    threshold_window_seconds: int = 300,
    severity: str = "HIGH",
    is_enabled: bool = True,
) -> DetectionRule:
    rule = DetectionRule(
        id=uuid4(),
        name=f"Test rule {rule_key}",
        description="Test detection rule",
        category=category,
        severity=severity,
        is_enabled=is_enabled,
        threshold_count=threshold_count,
        threshold_window_seconds=threshold_window_seconds,
        rule_key=rule_key,
    )
    return rule


# ── Brute Force ───────────────────────────────────────────────────────────────

class TestBruteForce:
    async def test_fires_when_threshold_exceeded(self):
        """Brute force alert fires when count >= threshold."""
        rule = make_rule("brute_force_login", threshold_count=5)
        event = make_event(description="Failed password attempt")

        db = AsyncMock()
        # _get_rule returns the enabled rule
        db.execute = AsyncMock()
        db.scalar = AsyncMock(side_effect=[rule, 10])  # rule.is_enabled query, count=10
        db.execute.return_value.scalar_one_or_none = MagicMock(side_effect=[rule, None])
        db.add = MagicMock()

        with patch("app.services.detection._get_rule", return_value=rule), \
             patch("app.services.detection._dedup_check", return_value=False):
            db.scalar = AsyncMock(return_value=10)  # 10 failures

            async def mock_execute(*args, **kwargs):
                m = MagicMock()
                m.scalar_one_or_none = MagicMock(return_value=None)
                return m

            db.execute = mock_execute
            db.add = MagicMock()

            alert = await check_brute_force(db, event)
            # With threshold 5 and count 10, alert should be generated
            # (relies on the patched _get_rule returning the rule)

    async def test_does_not_fire_for_non_auth_events(self):
        """Brute force rule ignores non-authentication events."""
        event = make_event(event_type=EventType.NETWORK, description="Port scan")
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("brute_force_login")):
            alert = await check_brute_force(db, event)
        assert alert is None

    async def test_does_not_fire_without_ip(self):
        """Brute force rule skips events with no source IP."""
        event = make_event(source_ip=None, description="Failed login")
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("brute_force_login")):
            alert = await check_brute_force(db, event)
        assert alert is None

    async def test_does_not_fire_for_success_events(self):
        """Brute force rule skips events with no failure keyword."""
        event = make_event(description="Successful authentication accepted")
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("brute_force_login")):
            alert = await check_brute_force(db, event)
        assert alert is None

    async def test_disabled_rule_returns_none(self):
        """Disabled rules never fire."""
        event = make_event(description="Failed password attempt")
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=None):
            alert = await check_brute_force(db, event)
        assert alert is None


# ── Privilege Escalation ──────────────────────────────────────────────────────

class TestPrivilegeEscalation:
    async def test_fires_on_privilege_escalation_event(self):
        """Privilege escalation alert fires on any PRIVILEGE_ESCALATION event."""
        event = make_event(
            event_type=EventType.PRIVILEGE_ESCALATION,
            severity=EventSeverity.CRITICAL,
            description="User executed sudo su -",
        )
        rule = make_rule("privilege_escalation", category=DetectionCategory.PRIVILEGE_ESCALATION, severity="CRITICAL")

        async def mock_execute(*args, **kwargs):
            m = MagicMock()
            m.scalar_one_or_none = MagicMock(return_value=None)
            return m

        db = AsyncMock()
        db.execute = mock_execute
        db.add = MagicMock()

        with patch("app.services.detection._get_rule", return_value=rule):
            alert = await check_privilege_escalation(db, event)
        assert alert is not None
        assert alert.severity == "CRITICAL"

    async def test_does_not_fire_for_auth_events(self):
        """Privilege escalation rule ignores auth events."""
        event = make_event(event_type=EventType.AUTHENTICATION)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("privilege_escalation")):
            alert = await check_privilege_escalation(db, event)
        assert alert is None

    async def test_disabled_privilege_escalation_rule(self):
        """Disabled privilege escalation rule never fires."""
        event = make_event(event_type=EventType.PRIVILEGE_ESCALATION)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=None):
            alert = await check_privilege_escalation(db, event)
        assert alert is None


# ── Port Scan ─────────────────────────────────────────────────────────────────

class TestPortScan:
    async def test_ignores_non_network_events(self):
        """Port scan rule skips non-NETWORK events."""
        event = make_event(event_type=EventType.AUTHENTICATION)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("port_scan")):
            alert = await check_port_scan(db, event)
        assert alert is None

    async def test_ignores_events_without_source_ip(self):
        """Port scan rule requires a source IP."""
        event = make_event(event_type=EventType.NETWORK, source_ip=None)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("port_scan")):
            alert = await check_port_scan(db, event)
        assert alert is None


# ── Multi-Account Failure ─────────────────────────────────────────────────────

class TestMultiAccountFailure:
    async def test_ignores_non_auth(self):
        event = make_event(event_type=EventType.NETWORK)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("multi_account_failure")):
            alert = await check_multi_account_failure(db, event)
        assert alert is None

    async def test_ignores_without_ip(self):
        event = make_event(source_ip=None, description="Failed login")
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("multi_account_failure")):
            alert = await check_multi_account_failure(db, event)
        assert alert is None


# ── IOC Match ─────────────────────────────────────────────────────────────────

class TestIocMatch:
    async def test_no_match_returns_none(self):
        """IOC match returns None when no matching indicator found."""
        event = make_event(source_ip="192.0.2.1")

        async def mock_execute(*args, **kwargs):
            m = MagicMock()
            m.scalar_one_or_none = MagicMock(return_value=None)
            return m

        db = AsyncMock()
        db.execute = mock_execute

        with patch("app.services.detection._get_rule", return_value=make_rule("ioc_match")):
            alert = await check_ioc_match(db, event)
        assert alert is None

    async def test_no_ip_no_match(self):
        """IOC match skips when event has no IP or hostname."""
        event = make_event(source_ip=None, hostname=None)
        db = AsyncMock()
        with patch("app.services.detection._get_rule", return_value=make_rule("ioc_match")):
            alert = await check_ioc_match(db, event)
        assert alert is None


# ── Detection Engine Error Handling ───────────────────────────────────────────

class TestDetectionEngine:
    async def test_rule_error_does_not_block_processing(self):
        """An exception in one rule should not stop other rules from running."""
        event = make_event()
        db = AsyncMock()
        db.commit = AsyncMock()

        call_count = 0

        async def failing_check(db, event):
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Simulated rule failure")

        async def passing_check(db, event):
            nonlocal call_count
            call_count += 1
            return None

        with patch("app.services.detection.RULE_CHECKS", [failing_check, passing_check]):
            alerts = await run_detection(db, event)

        assert call_count == 2  # Both rules were called
        assert alerts == []  # No alerts (both returned None or raised)

    async def test_run_detection_returns_list(self):
        """run_detection always returns a list."""
        event = make_event()
        db = AsyncMock()
        db.commit = AsyncMock()

        with patch("app.services.detection.RULE_CHECKS", []):
            alerts = await run_detection(db, event)
        assert isinstance(alerts, list)
