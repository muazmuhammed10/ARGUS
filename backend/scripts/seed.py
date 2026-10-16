"""
ARGUS — Development seed script.
Creates safe synthetic data: admin user, sample analysts, assets,
security events, incidents, and detection rules.

Usage:
    cd backend
    python -m scripts.seed

IMPORTANT: Never use real credentials, IP addresses of production
systems, or actual threat actor infrastructure in seed data.
All data here is clearly synthetic and for demonstration only.
"""

import asyncio
import random
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Load .env
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetEnvironment, AssetCriticality
from app.models.security_event import SecurityEvent, EventSeverity, EventType, DetectionStatus
from app.models.detection_rule import DetectionRule, DetectionCategory
from app.models.incident import Incident, IncidentSeverity, IncidentStatus
from app.models.indicator import Indicator, IndicatorType
from app.core.database import Base

# ── Synthetic data constants ────────────────────────────────────────────────
# These are RFC 5737 documentation IP ranges — safe to use in demos
SYNTHETIC_IPS = [
    "192.0.2.10", "192.0.2.45", "192.0.2.100", "192.0.2.200",
    "198.51.100.22", "198.51.100.77", "198.51.100.150",
    "203.0.113.5", "203.0.113.88", "203.0.113.200",
]
SYNTHETIC_HOSTNAMES = [
    "web-prod-01.argus.local", "db-prod-01.argus.local",
    "app-prod-02.argus.local", "mail-srv-01.argus.local",
    "vpn-gw-01.argus.local", "dev-workstation-07.argus.local",
    "ci-runner-03.argus.local",
]
SYNTHETIC_USERNAMES = [
    "jsmith", "alee", "mchen", "rjohnson", "kpatel",
    "admin_svc", "backup_svc", "root",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _ago(hours: int = 0, minutes: int = 0, days: int = 0) -> datetime:
    return _now() - timedelta(hours=hours, minutes=minutes, days=days)


async def seed(session: AsyncSession) -> None:
    print("🌱 Seeding ARGUS development database...")

    # ── 1. Users ──────────────────────────────────────────────────────────
    print("  Creating users...")

    admin = User(
        id=uuid.uuid4(),
        email=settings.SEED_ADMIN_EMAIL,
        username="admin",
        full_name="ARGUS Administrator",
        hashed_password=hash_password(settings.SEED_ADMIN_PASSWORD),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )

    analyst1 = User(
        id=uuid.uuid4(),
        email="analyst1@argus.local",
        username="analyst1",
        full_name="Alex Chen",
        hashed_password=hash_password("Analyst1Pass!23"),
        role=UserRole.SECURITY_ANALYST,
        is_active=True,
        is_verified=True,
    )

    analyst2 = User(
        id=uuid.uuid4(),
        email="analyst2@argus.local",
        username="analyst2",
        full_name="Morgan Riley",
        hashed_password=hash_password("Analyst2Pass!23"),
        role=UserRole.SECURITY_ANALYST,
        is_active=True,
        is_verified=True,
    )

    viewer = User(
        id=uuid.uuid4(),
        email="viewer@argus.local",
        username="viewer1",
        full_name="Sam Viewer",
        hashed_password=hash_password("Viewer1Pass!23"),
        role=UserRole.VIEWER,
        is_active=True,
        is_verified=True,
    )

    session.add_all([admin, analyst1, analyst2, viewer])
    await session.flush()

    # ── 2. Assets ──────────────────────────────────────────────────────────
    print("  Creating assets...")
    assets = [
        Asset(
            name="Production Web Server",
            hostname="web-prod-01.argus.local",
            ip_address="192.0.2.10",
            operating_system="Ubuntu 22.04 LTS",
            environment=AssetEnvironment.PRODUCTION,
            owner="Web Team",
            criticality=AssetCriticality.CRITICAL,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=1),
        ),
        Asset(
            name="Production Database",
            hostname="db-prod-01.argus.local",
            ip_address="192.0.2.45",
            operating_system="Ubuntu 22.04 LTS",
            environment=AssetEnvironment.PRODUCTION,
            owner="Database Team",
            criticality=AssetCriticality.CRITICAL,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=1),
        ),
        Asset(
            name="Application Server",
            hostname="app-prod-02.argus.local",
            ip_address="192.0.2.100",
            operating_system="CentOS Stream 9",
            environment=AssetEnvironment.PRODUCTION,
            owner="Platform Team",
            criticality=AssetCriticality.HIGH,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=2),
        ),
        Asset(
            name="Mail Server",
            hostname="mail-srv-01.argus.local",
            ip_address="192.0.2.200",
            operating_system="Ubuntu 20.04 LTS",
            environment=AssetEnvironment.PRODUCTION,
            owner="IT Operations",
            criticality=AssetCriticality.HIGH,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=3),
        ),
        Asset(
            name="VPN Gateway",
            hostname="vpn-gw-01.argus.local",
            ip_address="198.51.100.22",
            operating_system="pfSense 2.7",
            environment=AssetEnvironment.DMZ,
            owner="Network Team",
            criticality=AssetCriticality.CRITICAL,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(minutes=30),
        ),
        Asset(
            name="Developer Workstation 07",
            hostname="dev-workstation-07.argus.local",
            ip_address="198.51.100.77",
            operating_system="Windows 11 Pro",
            environment=AssetEnvironment.DEVELOPMENT,
            owner="Development Team",
            criticality=AssetCriticality.MEDIUM,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=5),
        ),
        Asset(
            name="CI/CD Runner 03",
            hostname="ci-runner-03.argus.local",
            ip_address="198.51.100.150",
            operating_system="Ubuntu 22.04 LTS",
            environment=AssetEnvironment.STAGING,
            owner="DevOps Team",
            criticality=AssetCriticality.MEDIUM,
            monitoring_status="ACTIVE",
            last_seen_at=_ago(hours=1),
        ),
    ]
    session.add_all(assets)
    await session.flush()

    # ── 3. Detection Rules ─────────────────────────────────────────────────
    print("  Creating detection rules...")
    rules = [
        DetectionRule(
            name="Brute Force Login Detection",
            description="Detects repeated failed SSH/login attempts from a single IP within a short window. Threshold: 10 failures in 5 minutes.",
            category=DetectionCategory.BRUTE_FORCE,
            severity="HIGH",
            is_enabled=True,
            threshold_count=10,
            threshold_window_seconds=300,
            rule_key="brute_force_login",
        ),
        DetectionRule(
            name="Successful Login After Multiple Failures",
            description="Detects a successful login following multiple failures — potential credential stuffing success.",
            category=DetectionCategory.CREDENTIAL_STUFFING,
            severity="HIGH",
            is_enabled=True,
            threshold_count=5,
            threshold_window_seconds=600,
            rule_key="success_after_failures",
        ),
        DetectionRule(
            name="Privilege Escalation Event",
            description="Detects unexpected privilege escalation such as sudo to root or UAC bypass patterns.",
            category=DetectionCategory.PRIVILEGE_ESCALATION,
            severity="CRITICAL",
            is_enabled=True,
            threshold_count=1,
            threshold_window_seconds=60,
            rule_key="privilege_escalation",
        ),
        DetectionRule(
            name="Port Scan Detection",
            description="Detects sequential port scanning patterns: single source IP touching many destination ports within 60 seconds.",
            category=DetectionCategory.PORT_SCAN,
            severity="MEDIUM",
            is_enabled=True,
            threshold_count=20,
            threshold_window_seconds=60,
            rule_key="port_scan",
        ),
        DetectionRule(
            name="Suspicious Admin Account Creation",
            description="Detects creation of new privileged accounts, especially outside business hours.",
            category=DetectionCategory.ACCOUNT_CREATION,
            severity="HIGH",
            is_enabled=True,
            threshold_count=1,
            threshold_window_seconds=3600,
            rule_key="admin_account_creation",
        ),
        DetectionRule(
            name="Multi-Account Authentication Failure",
            description="Detects one source IP failing to authenticate against multiple different user accounts — possible password spraying.",
            category=DetectionCategory.MULTI_ACCOUNT_FAILURE,
            severity="HIGH",
            is_enabled=True,
            threshold_count=5,
            threshold_window_seconds=300,
            rule_key="multi_account_failure",
        ),
        DetectionRule(
            name="Unusual Administrative Activity",
            description="Detects privileged commands executed at unusual hours or from unexpected source IPs.",
            category=DetectionCategory.ADMIN_ACTIVITY,
            severity="MEDIUM",
            is_enabled=True,
            threshold_count=3,
            threshold_window_seconds=1800,
            rule_key="unusual_admin_activity",
        ),
        DetectionRule(
            name="IOC Match",
            description="Matches event fields (IPs, domains, hashes) against the IOC database.",
            category=DetectionCategory.IOC_MATCH,
            severity="HIGH",
            is_enabled=True,
            threshold_count=1,
            threshold_window_seconds=60,
            rule_key="ioc_match",
        ),
    ]
    session.add_all(rules)
    await session.flush()

    # ── 4. Synthetic Security Events ──────────────────────────────────────
    print("  Creating synthetic security events (clearly marked is_synthetic=True)...")

    events = []

    # Brute-force SSH block
    for i in range(14):
        events.append(SecurityEvent(
            timestamp=_ago(hours=2, minutes=i * 2),
            source_system="SSH-Monitor (synthetic)",
            event_type=EventType.AUTHENTICATION,
            severity=EventSeverity.HIGH,
            source_ip="203.0.113.88",
            destination_ip="192.0.2.10",
            destination_port=22,
            username="root",
            hostname="web-prod-01.argus.local",
            description="[SYNTHETIC] Failed SSH authentication attempt",
            metadata_json={"attempt_number": i + 1, "auth_method": "password"},
            detection_status=DetectionStatus.UNREVIEWED,
            is_synthetic=True,
        ))

    # Successful login after failures
    events.append(SecurityEvent(
        timestamp=_ago(hours=1, minutes=55),
        source_system="SSH-Monitor (synthetic)",
        event_type=EventType.AUTHENTICATION,
        severity=EventSeverity.CRITICAL,
        source_ip="203.0.113.88",
        destination_ip="192.0.2.10",
        destination_port=22,
        username="root",
        hostname="web-prod-01.argus.local",
        description="[SYNTHETIC] Successful SSH login following 14 failed attempts — potential brute force success",
        metadata_json={"auth_method": "password", "preceded_by_failures": 14},
        detection_status=DetectionStatus.UNREVIEWED,
        is_synthetic=True,
    ))

    # Port scan pattern
    for port in [21, 22, 23, 25, 80, 443, 3306, 5432, 8080, 8443, 9200, 27017]:
        events.append(SecurityEvent(
            timestamp=_ago(hours=4, minutes=random.randint(0, 5)),
            source_system="Firewall-Log (synthetic)",
            event_type=EventType.NETWORK,
            severity=EventSeverity.MEDIUM,
            source_ip="198.51.100.150",
            destination_ip="192.0.2.45",
            destination_port=port,
            hostname="db-prod-01.argus.local",
            description=f"[SYNTHETIC] Connection probe to port {port} — possible port scan",
            metadata_json={"protocol": "TCP", "action": "REJECT"},
            detection_status=DetectionStatus.UNREVIEWED,
            is_synthetic=True,
        ))

    # Privilege escalation
    events.append(SecurityEvent(
        timestamp=_ago(hours=6),
        source_system="Linux-AuditD (synthetic)",
        event_type=EventType.PRIVILEGE_ESCALATION,
        severity=EventSeverity.CRITICAL,
        source_ip="192.0.2.100",
        username="jsmith",
        hostname="app-prod-02.argus.local",
        description="[SYNTHETIC] User jsmith executed sudo su - gaining root shell",
        metadata_json={"command": "sudo su -", "parent_process": "bash", "uid": 1001, "euid": 0},
        detection_status=DetectionStatus.UNREVIEWED,
        is_synthetic=True,
    ))

    # Admin account creation
    events.append(SecurityEvent(
        timestamp=_ago(hours=8),
        source_system="Linux-AuditD (synthetic)",
        event_type=EventType.AUTHORIZATION,
        severity=EventSeverity.HIGH,
        source_ip="192.0.2.10",
        username="admin_svc",
        hostname="web-prod-01.argus.local",
        description="[SYNTHETIC] New user account 'backdoor_svc' added to sudo group at 02:14 UTC",
        metadata_json={"new_username": "backdoor_svc", "groups": ["sudo", "adm"], "time_of_day": "02:14 UTC"},
        detection_status=DetectionStatus.UNREVIEWED,
        is_synthetic=True,
    ))

    # Normal auth events (green baseline)
    for i in range(20):
        username = random.choice(SYNTHETIC_USERNAMES[:5])
        ip = random.choice(SYNTHETIC_IPS[:4])
        events.append(SecurityEvent(
            timestamp=_ago(hours=random.randint(1, 48)),
            source_system="Windows-EventLog (synthetic)",
            event_type=EventType.AUTHENTICATION,
            severity=EventSeverity.INFO,
            source_ip=ip,
            username=username,
            hostname=random.choice(SYNTHETIC_HOSTNAMES),
            description=f"[SYNTHETIC] Successful interactive logon for {username}",
            metadata_json={"event_id": 4624, "logon_type": 2},
            detection_status=DetectionStatus.REVIEWED,
            is_synthetic=True,
        ))

    # Some policy violations
    for i in range(5):
        events.append(SecurityEvent(
            timestamp=_ago(days=random.randint(1, 3)),
            source_system="DLP-Monitor (synthetic)",
            event_type=EventType.POLICY_VIOLATION,
            severity=EventSeverity.MEDIUM,
            username=random.choice(SYNTHETIC_USERNAMES[:4]),
            hostname=random.choice(SYNTHETIC_HOSTNAMES[4:]),
            description="[SYNTHETIC] Large data transfer to external USB device detected",
            metadata_json={"bytes_transferred": random.randint(100_000_000, 2_000_000_000), "device_type": "USB"},
            detection_status=DetectionStatus.UNREVIEWED,
            is_synthetic=True,
        ))

    session.add_all(events)
    await session.flush()

    # ── 5. Incidents ────────────────────────────────────────────────────────
    print("  Creating incidents...")
    incident1 = Incident(
        title="Suspected Brute Force Attack on web-prod-01",
        description="[SYNTHETIC] 14 failed SSH attempts followed by a successful root login from external IP 203.0.113.88. Potential unauthorized access to production web server.",
        severity=IncidentSeverity.CRITICAL,
        status=IncidentStatus.INVESTIGATING,
        assigned_to_id=analyst1.id,
        created_by_id=admin.id,
        created_at=_ago(hours=1, minutes=50),
    )
    incident2 = Incident(
        title="Port Scanning Activity Detected on db-prod-01",
        description="[SYNTHETIC] Sequential connection attempts across 12 ports from CI runner IP. May indicate lateral movement or misconfigured scanner.",
        severity=IncidentSeverity.MEDIUM,
        status=IncidentStatus.TRIAGED,
        assigned_to_id=analyst2.id,
        created_by_id=admin.id,
        created_at=_ago(hours=3, minutes=30),
    )
    incident3 = Incident(
        title="Privilege Escalation: jsmith on app-prod-02",
        description="[SYNTHETIC] User jsmith executed sudo su - gaining root shell. Requires verification of change management record.",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.NEW,
        assigned_to_id=None,
        created_by_id=admin.id,
        created_at=_ago(hours=6),
    )

    session.add_all([incident1, incident2, incident3])
    await session.flush()

    # ── 6. IOC Indicators ──────────────────────────────────────────────────
    print("  Creating sample IOC indicators...")
    iocs = [
        Indicator(
            value="203.0.113.88",
            indicator_type=IndicatorType.IPV4,
            confidence=0.85,
            is_malicious=True,
            analyst_notes="[SYNTHETIC] Source IP for brute force attempts on web-prod-01. RFC 5737 test address.",
            tags="brute-force,ssh",
            source="analyst-observation",
            first_seen_at=_ago(hours=2),
            last_seen_at=_ago(hours=1, minutes=55),
        ),
        Indicator(
            value="198.51.100.150",
            indicator_type=IndicatorType.IPV4,
            confidence=0.60,
            is_malicious=None,
            analyst_notes="[SYNTHETIC] Source of port scan activity. Could be internal scanner. Under investigation.",
            tags="port-scan,investigation",
            source="firewall-alert",
            first_seen_at=_ago(hours=4),
            last_seen_at=_ago(hours=4),
        ),
        Indicator(
            value="malware-c2-example.invalid",
            indicator_type=IndicatorType.DOMAIN,
            confidence=0.95,
            is_malicious=True,
            analyst_notes="[SYNTHETIC] Example C2 domain for demo purposes. .invalid TLD ensures no real DNS resolution.",
            tags="c2,malware",
            source="threat-feed-demo",
            first_seen_at=_ago(days=7),
            last_seen_at=_ago(days=1),
        ),
        Indicator(
            value="44d88612fea8a8f36de82e1278abb02f",  # MD5 of EICAR test string
            indicator_type=IndicatorType.MD5,
            confidence=1.0,
            is_malicious=True,
            analyst_notes="[SYNTHETIC] EICAR antivirus test file MD5 — safe for demo IOC matching.",
            tags="eicar,test,antivirus",
            source="demo-data",
            first_seen_at=_ago(days=14),
            last_seen_at=_ago(days=3),
        ),
    ]
    session.add_all(iocs)
    await session.flush()

    await session.commit()
    print("✅ Seed completed successfully.")
    print(f"   Admin: {settings.SEED_ADMIN_EMAIL} / {settings.SEED_ADMIN_PASSWORD}")
    print("   Analyst: analyst1@argus.local / Analyst1Pass!23")
    print("   Analyst: analyst2@argus.local / Analyst2Pass!23")
    print("   Viewer:  viewer@argus.local / Viewer1Pass!23")
    print("   ⚠️  Change all passwords before any non-local deployment.")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        await seed(session)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
