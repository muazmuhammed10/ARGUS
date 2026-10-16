"""ARGUS — Asset inventory model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_types import SmartUUID


class AssetEnvironment(str, enum.Enum):
    PRODUCTION = "PRODUCTION"
    STAGING = "STAGING"
    DEVELOPMENT = "DEVELOPMENT"
    CORPORATE = "CORPORATE"
    DMZ = "DMZ"
    UNKNOWN = "UNKNOWN"


class AssetCriticality(str, enum.Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True, index=True)
    operating_system: Mapped[str | None] = mapped_column(String(255), nullable=True)
    environment: Mapped[AssetEnvironment] = mapped_column(Enum(AssetEnvironment, name="asset_environment"), nullable=False, default=AssetEnvironment.UNKNOWN)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[AssetCriticality] = mapped_column(Enum(AssetCriticality, name="asset_criticality"), nullable=False, default=AssetCriticality.MEDIUM)
    monitoring_status: Mapped[str] = mapped_column(String(64), default="ACTIVE", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
