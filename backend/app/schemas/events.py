"""ARGUS — Security event schemas."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.security_event import EventSeverity, EventType, DetectionStatus


class EventIngestRequest(BaseModel):
    """Single event ingestion payload."""
    timestamp: Optional[datetime] = None
    source_system: str = Field(min_length=1, max_length=255)
    event_type: EventType
    severity: EventSeverity
    source_ip: Optional[str] = Field(None, max_length=45)
    destination_ip: Optional[str] = Field(None, max_length=45)
    source_port: Optional[int] = Field(None, ge=0, le=65535)
    destination_port: Optional[int] = Field(None, ge=0, le=65535)
    username: Optional[str] = Field(None, max_length=255)
    hostname: Optional[str] = Field(None, max_length=255)
    description: str = Field(min_length=1, max_length=10000)
    metadata_json: Optional[dict[str, Any]] = None
    is_synthetic: bool = False

    @field_validator("source_ip", "destination_ip", mode="before")
    @classmethod
    def validate_ip(cls, v):
        if v is None:
            return v
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")
        return v


class EventResponse(BaseModel):
    id: UUID
    timestamp: datetime
    source_system: str
    event_type: EventType
    severity: EventSeverity
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    username: Optional[str] = None
    hostname: Optional[str] = None
    description: str
    metadata_json: Optional[dict[str, Any]] = None
    detection_status: DetectionStatus
    is_synthetic: bool
    incident_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    page: int
    page_size: int
