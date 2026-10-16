"""ARGUS — Investigation model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID


class InvestigationStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    CLOSED = "CLOSED"


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InvestigationStatus] = mapped_column(Enum(InvestigationStatus, name="investigation_status"), nullable=False, default=InvestigationStatus.OPEN)
    hypothesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident: Mapped["Incident | None"] = relationship("Incident", back_populates="investigations")
    notes: Mapped[list["InvestigationNote"]] = relationship("InvestigationNote", back_populates="investigation", cascade="all, delete-orphan")
    evidence: Mapped[list["InvestigationEvidence"]] = relationship("InvestigationEvidence", back_populates="investigation", cascade="all, delete-orphan")
    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_id])
    assigned_to: Mapped["User | None"] = relationship("User", foreign_keys=[assigned_to_id])

    def __repr__(self) -> str:
        return f"<Investigation id={self.id} status={self.status}>"
