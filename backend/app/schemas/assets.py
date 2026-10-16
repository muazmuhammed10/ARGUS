"""ARGUS — Asset schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.asset import AssetEnvironment, AssetCriticality


class AssetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    operating_system: Optional[str] = Field(None, max_length=255)
    environment: AssetEnvironment = AssetEnvironment.UNKNOWN
    owner: Optional[str] = Field(None, max_length=255)
    criticality: AssetCriticality = AssetCriticality.MEDIUM
    monitoring_status: str = "ACTIVE"
    notes: Optional[str] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    hostname: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    operating_system: Optional[str] = Field(None, max_length=255)
    environment: Optional[AssetEnvironment] = None
    owner: Optional[str] = Field(None, max_length=255)
    criticality: Optional[AssetCriticality] = None
    monitoring_status: Optional[str] = None
    notes: Optional[str] = None


class AssetResponse(BaseModel):
    id: UUID
    name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    operating_system: Optional[str] = None
    environment: AssetEnvironment
    owner: Optional[str] = None
    criticality: AssetCriticality
    monitoring_status: str
    notes: Optional[str] = None
    last_seen_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AssetListResponse(BaseModel):
    items: list[AssetResponse]
    total: int
    page: int
    page_size: int
