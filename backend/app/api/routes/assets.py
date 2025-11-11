from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.asset import AssetCreate, AssetRead, AssetUpdate, AssetQuery
from app.repositories.asset_repo import AssetRepository

router = APIRouter(prefix="/assets", tags=["assets"])

@router.post("", response_model=AssetRead, status_code=201)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    try:
        return repo.create(payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("", response_model=dict)
def list_assets(
    symbol: str | None = None,
    exchange: str | None = None,
    asset_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query("symbol", pattern="^(created_at|updated_at|symbol|exchange|asset_type|name)$"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    repo = AssetRepository(db)
    q = AssetQuery(
        symbol=symbol,
        exchange=exchange,
        asset_type=asset_type,  # pydantic will validate enum literal
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )
    rows, total = repo.list_and_count(q)
    return {
        "items": rows,
        "total": total,
        "limit": limit,
        "offset": offset,
    }

@router.get("/{asset_id}", response_model=AssetRead)
def get_asset(asset_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    entity = repo.get(asset_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Asset not found")
    return entity

@router.patch("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: str, patch: AssetUpdate, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    entity = repo.get(asset_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Asset not found")
    try:
        return repo.update(entity, patch)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.delete("/{asset_id}", status_code=204)
def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    repo = AssetRepository(db)
    entity = repo.get(asset_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Asset not found")
    repo.delete(entity)
    return None
