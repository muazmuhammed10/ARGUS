"""ARGUS — Incident schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=512)
    description: str = Field(min_length=3)
    severity: IncidentSeverity
    assigned_to_id: Optional[UUID] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=512)
    description: Optional[str] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    assigned_to_id: Optional[UUID] = None
    remediation_summary: Optional[str] = None
    resolution_summary: Optional[str] = None


class IncidentResponse(BaseModel):
    id: UUID
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    assigned_to_id: Optional[UUID] = None
    created_by_id: UUID
    remediation_summary: Optional[str] = None
    resolution_summary: Optional[str] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    page: int
    page_size: int
