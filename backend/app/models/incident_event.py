"""ARGUS — Incident-Event association."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base_types import SmartUUID


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(SmartUUID(), ForeignKey("security_events.id", ondelete="CASCADE"), nullable=False, index=True)
    analyst_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    added_by_id: Mapped[uuid.UUID | None] = mapped_column(SmartUUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
