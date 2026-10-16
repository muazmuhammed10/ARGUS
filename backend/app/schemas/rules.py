"""ARGUS — Detection rule schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.detection_rule import DetectionCategory


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    severity: Optional[str] = None
    is_enabled: Optional[bool] = None
    threshold_count: Optional[int] = Field(None, ge=1, le=10000)
    threshold_window_seconds: Optional[int] = Field(None, ge=10, le=86400)


class RuleResponse(BaseModel):
    id: UUID
    name: str
    description: str
    category: DetectionCategory
    severity: str
    is_enabled: bool
    threshold_count: int
    threshold_window_seconds: int
    rule_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RuleListResponse(BaseModel):
    items: list[RuleResponse]
    total: int
