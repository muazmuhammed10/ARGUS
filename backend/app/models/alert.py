"""ARGUS — Alert model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID, SmartJSON


class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus, name="alert_status"), nullable=False, default=AlertStatus.OPEN, index=True)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("detection_rules.id", ondelete="SET NULL"), nullable=True)
    event_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("security_events.id", ondelete="SET NULL"), nullable=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(SmartJSON(), nullable=True)
    dedup_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    occurrence_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    rule: Mapped["DetectionRule | None"] = relationship("DetectionRule", back_populates="alerts")
    event: Mapped["SecurityEvent | None"] = relationship("SecurityEvent", back_populates="alerts")
    incident: Mapped["Incident | None"] = relationship("Incident", back_populates="alerts")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} severity={self.severity} status={self.status}>"
