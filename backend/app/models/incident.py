"""ARGUS — Incident model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID


class IncidentSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    TRIAGED = "TRIAGED"
    INVESTIGATING = "INVESTIGATING"
    CONTAINED = "CONTAINED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(Enum(IncidentSeverity, name="incident_severity"), nullable=False, index=True)
    status: Mapped[IncidentStatus] = mapped_column(Enum(IncidentStatus, name="incident_status"), nullable=False, default=IncidentStatus.NEW, index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    remediation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    events: Mapped[list["SecurityEvent"]] = relationship("SecurityEvent", back_populates="incident")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="incident")
    assigned_to: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to_id])
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    investigations: Mapped[list["Investigation"]] = relationship("Investigation", back_populates="incident")

    def __repr__(self) -> str:
        return f"<Incident id={self.id} status={self.status} severity={self.severity}>"
