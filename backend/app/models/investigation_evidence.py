"""ARGUS — Investigation evidence model."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    collected_by_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="evidence")
