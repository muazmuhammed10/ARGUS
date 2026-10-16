"""initial_schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2024-01-01 00:00:00.000000

This migration creates the full initial ARGUS database schema.
It is safe to apply against a fresh database.
If tables already exist (created via create_all during Phase 1),
run: alembic stamp head  — to mark them as migrated without recreating.
"""

from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ──────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE user_role AS ENUM ('ADMIN', 'SECURITY_ANALYST', 'VIEWER')")
    op.execute("CREATE TYPE asset_environment AS ENUM ('PRODUCTION','STAGING','DEVELOPMENT','CORPORATE','DMZ','UNKNOWN')")
    op.execute("CREATE TYPE asset_criticality AS ENUM ('CRITICAL','HIGH','MEDIUM','LOW')")
    op.execute("CREATE TYPE event_severity AS ENUM ('CRITICAL','HIGH','MEDIUM','LOW','INFO')")
    op.execute("CREATE TYPE event_type AS ENUM ('AUTHENTICATION','AUTHORIZATION','NETWORK','ENDPOINT','MALWARE','POLICY_VIOLATION','PRIVILEGE_ESCALATION','RECONNAISSANCE','DATA_EXFILTRATION','SYSTEM','OTHER')")
    op.execute("CREATE TYPE detection_status AS ENUM ('UNREVIEWED','REVIEWED','FALSE_POSITIVE','ESCALATED')")
    op.execute("CREATE TYPE detection_category AS ENUM ('BRUTE_FORCE','CREDENTIAL_STUFFING','PRIVILEGE_ESCALATION','PORT_SCAN','LATERAL_MOVEMENT','ACCOUNT_CREATION','ADMIN_ACTIVITY','IOC_MATCH','MULTI_ACCOUNT_FAILURE','CUSTOM')")
    op.execute("CREATE TYPE alert_status AS ENUM ('OPEN','ACKNOWLEDGED','RESOLVED','FALSE_POSITIVE')")
    op.execute("CREATE TYPE incident_severity AS ENUM ('CRITICAL','HIGH','MEDIUM','LOW')")
    op.execute("CREATE TYPE incident_status AS ENUM ('NEW','TRIAGED','INVESTIGATING','CONTAINED','RESOLVED','CLOSED')")
    op.execute("CREATE TYPE indicator_type AS ENUM ('IPV4','IPV6','DOMAIN','URL','MD5','SHA1','SHA256','EMAIL','CVE')")
    op.execute("CREATE TYPE investigation_status AS ENUM ('OPEN','IN_PROGRESS','ON_HOLD','CLOSED')")
    op.execute("CREATE TYPE note_type AS ENUM ('OBSERVATION','HYPOTHESIS','EVIDENCE','ACTION','AI_GENERATED')")

    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(512), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "SECURITY_ANALYST", "VIEWER", name="user_role", create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("password_reset_token", sa.String(512), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    # ── refresh_tokens ─────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(512), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)

    # ── assets ─────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("operating_system", sa.String(255), nullable=True),
        sa.Column("environment", sa.Enum("PRODUCTION","STAGING","DEVELOPMENT","CORPORATE","DMZ","UNKNOWN", name="asset_environment", create_type=False), nullable=False),
        sa.Column("owner", sa.String(255), nullable=True),
        sa.Column("criticality", sa.Enum("CRITICAL","HIGH","MEDIUM","LOW", name="asset_criticality", create_type=False), nullable=False),
        sa.Column("monitoring_status", sa.String(64), nullable=False, server_default="ACTIVE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_assets_id", "assets", ["id"])
    op.create_index("ix_assets_hostname", "assets", ["hostname"])
    op.create_index("ix_assets_ip_address", "assets", ["ip_address"])

    # ── detection_rules ────────────────────────────────────────────────────
    op.create_table(
        "detection_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.Enum("BRUTE_FORCE","CREDENTIAL_STUFFING","PRIVILEGE_ESCALATION","PORT_SCAN","LATERAL_MOVEMENT","ACCOUNT_CREATION","ADMIN_ACTIVITY","IOC_MATCH","MULTI_ACCOUNT_FAILURE","CUSTOM", name="detection_category", create_type=False), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("threshold_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("threshold_window_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("rule_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("rule_key"),
    )
    op.create_index("ix_detection_rules_id", "detection_rules", ["id"])

    # ── incidents ──────────────────────────────────────────────────────────
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.Enum("CRITICAL","HIGH","MEDIUM","LOW", name="incident_severity", create_type=False), nullable=False),
        sa.Column("status", sa.Enum("NEW","TRIAGED","INVESTIGATING","CONTAINED","RESOLVED","CLOSED", name="incident_status", create_type=False), nullable=False, server_default="NEW"),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("remediation_summary", sa.Text(), nullable=True),
        sa.Column("resolution_summary", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])

    # ── security_events ────────────────────────────────────────────────────
    op.create_table(
        "security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_system", sa.String(255), nullable=False),
        sa.Column("event_type", sa.Enum("AUTHENTICATION","AUTHORIZATION","NETWORK","ENDPOINT","MALWARE","POLICY_VIOLATION","PRIVILEGE_ESCALATION","RECONNAISSANCE","DATA_EXFILTRATION","SYSTEM","OTHER", name="event_type", create_type=False), nullable=False),
        sa.Column("severity", sa.Enum("CRITICAL","HIGH","MEDIUM","LOW","INFO", name="event_severity", create_type=False), nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=True),
        sa.Column("destination_ip", sa.String(45), nullable=True),
        sa.Column("source_port", sa.Integer(), nullable=True),
        sa.Column("destination_port", sa.Integer(), nullable=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("hostname", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("detection_status", sa.Enum("UNREVIEWED","REVIEWED","FALSE_POSITIVE","ESCALATED", name="detection_status", create_type=False), nullable=False, server_default="UNREVIEWED"),
        sa.Column("is_synthetic", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("dedup_hash", sa.String(64), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_security_events_id", "security_events", ["id"])
    op.create_index("ix_security_events_timestamp", "security_events", ["timestamp"])
    op.create_index("ix_security_events_source_system", "security_events", ["source_system"])
    op.create_index("ix_security_events_event_type", "security_events", ["event_type"])
    op.create_index("ix_security_events_severity", "security_events", ["severity"])
    op.create_index("ix_security_events_source_ip", "security_events", ["source_ip"])
    op.create_index("ix_security_events_username", "security_events", ["username"])
    op.create_index("ix_security_events_hostname", "security_events", ["hostname"])
    op.create_index("ix_security_events_dedup_hash", "security_events", ["dedup_hash"])
    op.create_index("ix_security_events_incident_id", "security_events", ["incident_id"])
    op.create_index("ix_security_events_timestamp_severity", "security_events", ["timestamp", "severity"])
    op.create_index("ix_security_events_source_ip_timestamp", "security_events", ["source_ip", "timestamp"])

    # ── alerts ─────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("status", sa.Enum("OPEN","ACKNOWLEDGED","RESOLVED","FALSE_POSITIVE", name="alert_status", create_type=False), nullable=False, server_default="OPEN"),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("dedup_key", sa.String(128), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("occurrence_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["rule_id"], ["detection_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["event_id"], ["security_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alerts_id", "alerts", ["id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_dedup_key", "alerts", ["dedup_key"])

    # ── incident_events ────────────────────────────────────────────────────
    op.create_table(
        "incident_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("analyst_note", sa.Text(), nullable=True),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("added_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["security_events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["added_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_events_incident_id", "incident_events", ["incident_id"])
    op.create_index("ix_incident_events_event_id", "incident_events", ["event_id"])

    # ── indicators_of_compromise ───────────────────────────────────────────
    op.create_table(
        "indicators_of_compromise",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.String(512), nullable=False),
        sa.Column("indicator_type", sa.Enum("IPV4","IPV6","DOMAIN","URL","MD5","SHA1","SHA256","EMAIL","CVE", name="indicator_type", create_type=False), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("is_malicious", sa.Boolean(), nullable=True),
        sa.Column("reputation_score", sa.Integer(), nullable=True),
        sa.Column("analyst_notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.String(512), nullable=True),
        sa.Column("source", sa.String(255), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_indicators_of_compromise_id", "indicators_of_compromise", ["id"])
    op.create_index("ix_indicators_of_compromise_value", "indicators_of_compromise", ["value"])
    op.create_index("ix_indicators_of_compromise_indicator_type", "indicators_of_compromise", ["indicator_type"])

    # ── threat_intelligence_results ────────────────────────────────────────
    op.create_table(
        "threat_intelligence_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("indicator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("raw_response", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_malicious", sa.Boolean(), nullable=True),
        sa.Column("reputation_score", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("tags", sa.String(512), nullable=True),
        sa.Column("error_message", sa.String(512), nullable=True),
        sa.Column("is_cached", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("queried_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("queried_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["indicator_id"], ["indicators_of_compromise.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["queried_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_threat_intelligence_results_id", "threat_intelligence_results", ["id"])
    op.create_index("ix_threat_intelligence_results_indicator_id", "threat_intelligence_results", ["indicator_id"])

    # ── investigations ─────────────────────────────────────────────────────
    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("OPEN","IN_PROGRESS","ON_HOLD","CLOSED", name="investigation_status", create_type=False), nullable=False, server_default="OPEN"),
        sa.Column("hypothesis", sa.Text(), nullable=True),
        sa.Column("final_conclusion", sa.Text(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_to_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigations_id", "investigations", ["id"])
    op.create_index("ix_investigations_incident_id", "investigations", ["incident_id"])

    # ── investigation_notes ────────────────────────────────────────────────
    op.create_table(
        "investigation_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("note_type", sa.Enum("OBSERVATION","HYPOTHESIS","EVIDENCE","ACTION","AI_GENERATED", name="note_type", create_type=False), nullable=False, server_default="OBSERVATION"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_notes_investigation_id", "investigation_notes", ["investigation_id"])

    # ── investigation_evidence ─────────────────────────────────────────────
    op.create_table(
        "investigation_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_type", sa.String(64), nullable=False),
        sa.Column("reference_id", sa.String(128), nullable=True),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("collected_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["collected_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigation_evidence_investigation_id", "investigation_evidence", ["investigation_id"])

    # ── audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("resource_type", sa.String(64), nullable=True),
        sa.Column("resource_id", sa.String(128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("extra_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("investigation_evidence")
    op.drop_table("investigation_notes")
    op.drop_table("investigations")
    op.drop_table("threat_intelligence_results")
    op.drop_table("indicators_of_compromise")
    op.drop_table("incident_events")
    op.drop_table("alerts")
    op.drop_table("security_events")
    op.drop_table("incidents")
    op.drop_table("detection_rules")
    op.drop_table("assets")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS note_type")
    op.execute("DROP TYPE IF EXISTS investigation_status")
    op.execute("DROP TYPE IF EXISTS indicator_type")
    op.execute("DROP TYPE IF EXISTS incident_status")
    op.execute("DROP TYPE IF EXISTS incident_severity")
    op.execute("DROP TYPE IF EXISTS alert_status")
    op.execute("DROP TYPE IF EXISTS detection_category")
    op.execute("DROP TYPE IF EXISTS detection_status")
    op.execute("DROP TYPE IF EXISTS event_type")
    op.execute("DROP TYPE IF EXISTS event_severity")
    op.execute("DROP TYPE IF EXISTS asset_criticality")
    op.execute("DROP TYPE IF EXISTS asset_environment")
    op.execute("DROP TYPE IF EXISTS user_role")
