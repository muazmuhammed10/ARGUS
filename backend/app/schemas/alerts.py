"""ARGUS — Alert schemas."""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel

from app.models.alert import AlertStatus


class AlertResponse(BaseModel):
    id: UUID
    title: str
    description: str
    severity: str
    status: AlertStatus
    rule_id: Optional[UUID] = None
    event_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    evidence: Optional[dict[str, Any]] = None
    dedup_key: Optional[str] = None
    occurrence_count: int
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AlertUpdate(BaseModel):
    status: AlertStatus


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    page: int
    page_size: int
