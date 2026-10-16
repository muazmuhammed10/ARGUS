"""ARGUS — Investigation schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.investigation import InvestigationStatus
from app.models.investigation_note import NoteType


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=3, max_length=512)
    description: Optional[str] = None
    incident_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    hypothesis: Optional[str] = None


class InvestigationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=512)
    description: Optional[str] = None
    status: Optional[InvestigationStatus] = None
    assigned_to_id: Optional[UUID] = None
    hypothesis: Optional[str] = None
    final_conclusion: Optional[str] = None


class InvestigationResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    status: InvestigationStatus
    hypothesis: Optional[str] = None
    final_conclusion: Optional[str] = None
    ai_summary: Optional[str] = None
    incident_id: Optional[UUID] = None
    assigned_to_id: Optional[UUID] = None
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InvestigationListResponse(BaseModel):
    items: list[InvestigationResponse]
    total: int
    page: int
    page_size: int


class NoteCreate(BaseModel):
    content: str = Field(min_length=1)
    note_type: NoteType = NoteType.OBSERVATION


class NoteResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    author_id: Optional[UUID] = None
    note_type: NoteType
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
