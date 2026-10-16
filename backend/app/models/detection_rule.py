"""ARGUS — Detection rule model."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base_types import SmartUUID


class DetectionCategory(str, enum.Enum):
    BRUTE_FORCE = "BRUTE_FORCE"
    CREDENTIAL_STUFFING = "CREDENTIAL_STUFFING"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    PORT_SCAN = "PORT_SCAN"
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"
    ACCOUNT_CREATION = "ACCOUNT_CREATION"
    ADMIN_ACTIVITY = "ADMIN_ACTIVITY"
    IOC_MATCH = "IOC_MATCH"
    MULTI_ACCOUNT_FAILURE = "MULTI_ACCOUNT_FAILURE"
    CUSTOM = "CUSTOM"


class DetectionRule(Base):
    __tablename__ = "detection_rules"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[DetectionCategory] = mapped_column(Enum(DetectionCategory, name="detection_category"), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="MEDIUM")
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    threshold_count: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    threshold_window_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    rule_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), nullable=True)

    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="rule")

    def __repr__(self) -> str:
        return f"<DetectionRule id={self.id} name={self.name} enabled={self.is_enabled}>"
