"""ARGUS — Indicators of Compromise model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, String, Text, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID


class IndicatorType(str, enum.Enum):
    IPV4 = "IPV4"
    IPV6 = "IPV6"
    DOMAIN = "DOMAIN"
    URL = "URL"
    MD5 = "MD5"
    SHA1 = "SHA1"
    SHA256 = "SHA256"
    EMAIL = "EMAIL"
    CVE = "CVE"


class Indicator(Base):
    __tablename__ = "indicators_of_compromise"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    indicator_type: Mapped[IndicatorType] = mapped_column(Enum(IndicatorType, name="indicator_type"), nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_malicious: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reputation_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), nullable=True)

    threat_intel_results: Mapped[list["ThreatIntelResult"]] = relationship("ThreatIntelResult", back_populates="indicator")

    def __repr__(self) -> str:
        return f"<Indicator type={self.indicator_type} value={self.value[:32]}>"
