"""ARGUS — Security event model (normalized event schema)."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID, SmartJSON


class EventSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EventType(str, enum.Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    NETWORK = "NETWORK"
    ENDPOINT = "ENDPOINT"
    MALWARE = "MALWARE"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    RECONNAISSANCE = "RECONNAISSANCE"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    SYSTEM = "SYSTEM"
    OTHER = "OTHER"


class DetectionStatus(str, enum.Enum):
    UNREVIEWED = "UNREVIEWED"
    REVIEWED = "REVIEWED"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    ESCALATED = "ESCALATED"


class SecurityEvent(Base):
    __tablename__ = "security_events"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    source_system: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, name="event_type"), nullable=False, index=True)
    severity: Mapped[EventSeverity] = mapped_column(Enum(EventSeverity, name="event_severity"), nullable=False, index=True)
    source_ip: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    destination_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    source_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(SmartJSON(), nullable=True)
    detection_status: Mapped[DetectionStatus] = mapped_column(Enum(DetectionStatus, name="detection_status"), nullable=False, default=DetectionStatus.UNREVIEWED)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dedup_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    incident: Mapped["Incident | None"] = relationship("Incident", back_populates="events")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="event")

    def __repr__(self) -> str:
        return f"<SecurityEvent id={self.id} type={self.event_type} severity={self.severity}>"
