"""ARGUS — Asset inventory endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import AnyRole, AnalystOrAdmin
from app.core.database import get_db
from app.models.asset import Asset, AssetEnvironment, AssetCriticality
from app.schemas.assets import (
    AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
)

router = APIRouter()


@router.get("", response_model=AssetListResponse)
async def list_assets(
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    environment: Optional[AssetEnvironment] = Query(None),
    criticality: Optional[AssetCriticality] = Query(None),
    search: Optional[str] = Query(None, max_length=255),
):
    conditions = []
    if environment:
        conditions.append(Asset.environment == environment)
    if criticality:
        conditions.append(Asset.criticality == criticality)
    if search:
        conditions.append(or_(
            Asset.name.ilike(f"%{search}%"),
            Asset.hostname.ilike(f"%{search}%"),
            Asset.ip_address.ilike(f"%{search}%"),
            Asset.owner.ilike(f"%{search}%"),
        ))

    where = and_(*conditions) if conditions else True
    total = await db.scalar(select(func.count(Asset.id)).where(where)) or 0
    result = await db.execute(
        select(Asset).where(where)
        .order_by(Asset.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return AssetListResponse(
        items=[AssetResponse.model_validate(a) for a in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
async def create_asset(
    payload: AssetCreate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    asset = Asset(**payload.model_dump())
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return AssetResponse.model_validate(asset)


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    current_user: AnyRole,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return AssetResponse.model_validate(asset)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, val)

    await db.commit()
    await db.refresh(asset)
    return AssetResponse.model_validate(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    current_user: AnalystOrAdmin,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Asset).where(Asset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(asset)
    await db.commit()
