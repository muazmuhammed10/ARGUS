"""ARGUS — Investigation workspace endpoints."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin
from app.core.database import get_db
from app.models.investigation import Investigation, InvestigationStatus
from app.models.investigation_note import InvestigationNote
from app.schemas.investigations import (
    InvestigationCreate, InvestigationUpdate, InvestigationResponse,
    InvestigationListResponse, NoteCreate, NoteResponse,
)

router = APIRouter()


@router.get("", response_model=InvestigationListResponse)
async def list_investigations(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    inv_status: Optional[InvestigationStatus] = Query(None, alias="status"),
    search: Optional[str] = Query(None, max_length=255),
):
    from sqlalchemy import or_
    conditions = []
    if inv_status:
        conditions.append(Investigation.status == inv_status)
    if search:
        conditions.append(or_(
            Investigation.title.ilike(f"%{search}%"),
            Investigation.description.ilike(f"%{search}%"),
        ))

    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(Investigation.id)).where(where)) or 0
    result = await db.execute(
        select(Investigation).where(where)
        .order_by(Investigation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return InvestigationListResponse(
        items=[InvestigationResponse.model_validate(i) for i in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=InvestigationResponse, status_code=status.HTTP_201_CREATED)
async def create_investigation(
    payload: InvestigationCreate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    inv = Investigation(
        title=payload.title,
        description=payload.description,
        incident_id=payload.incident_id,
        assigned_to_id=payload.assigned_to_id,
        hypothesis=payload.hypothesis,
        created_by_id=current_user.id,
        status=InvestigationStatus.OPEN,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    return InvestigationResponse.model_validate(inv)


@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return InvestigationResponse.model_validate(inv)


@router.patch("/{investigation_id}", response_model=InvestigationResponse)
async def update_investigation(
    investigation_id: UUID,
    payload: InvestigationUpdate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Investigation).where(Investigation.id == investigation_id))
    inv = result.scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(inv, field, val)

    if payload.inv_status == InvestigationStatus.CLOSED and not inv.closed_at:
        inv.closed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(inv)
    return InvestigationResponse.model_validate(inv)


# ── Notes ─────────────────────────────────────────────────────────────────────

@router.post("/{investigation_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def add_note(
    investigation_id: UUID,
    payload: NoteCreate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    inv_r = await db.execute(select(Investigation.id).where(Investigation.id == investigation_id))
    if not inv_r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Investigation not found")

    note = InvestigationNote(
        investigation_id=investigation_id,
        author_id=current_user.id,
        note_type=payload.note_type,
        content=payload.content,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get("/{investigation_id}/notes", response_model=list[NoteResponse])
async def list_notes(
    investigation_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InvestigationNote)
        .where(InvestigationNote.investigation_id == investigation_id)
        .order_by(InvestigationNote.created_at.asc())
    )
    return [NoteResponse.model_validate(n) for n in result.scalars().all()]
