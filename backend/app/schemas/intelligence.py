"""ARGUS — Threat intelligence schemas."""
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.indicator import IndicatorType


class IndicatorLookupRequest(BaseModel):
    value: str = Field(min_length=1, max_length=512)
    indicator_type: IndicatorType
    analyst_notes: Optional[str] = None


class IndicatorResponse(BaseModel):
    id: UUID
    value: str
    indicator_type: IndicatorType
    confidence: Optional[float] = None
    is_malicious: Optional[bool] = None
    reputation_score: Optional[int] = None
    analyst_notes: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IndicatorListResponse(BaseModel):
    items: list[IndicatorResponse]
    total: int
    page: int
    page_size: int


class ThreatIntelResultResponse(BaseModel):
    id: UUID
    indicator_id: UUID
    provider: str
    is_malicious: Optional[bool] = None
    reputation_score: Optional[int] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    error_message: Optional[str] = None
    is_cached: bool
    queried_at: datetime

    model_config = {"from_attributes": True}
