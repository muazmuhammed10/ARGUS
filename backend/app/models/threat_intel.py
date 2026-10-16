"""ARGUS — Threat intelligence lookup result model."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID, SmartJSON


class ThreatIntelResult(Base):
    __tablename__ = "threat_intelligence_results"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    indicator_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("indicators_of_compromise.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_response: Mapped[dict | None] = mapped_column(SmartJSON(), nullable=True)
    is_malicious: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reputation_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_cached: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    queried_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    queried_by_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    indicator: Mapped["Indicator"] = relationship("Indicator", back_populates="threat_intel_results")

    def __repr__(self) -> str:
        return f"<ThreatIntelResult provider={self.provider} indicator_id={self.indicator_id}>"
