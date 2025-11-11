from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.api.deps import get_db
from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyOut

router = APIRouter()

def _get(db: Session, sid: int) -> Strategy:
    obj = db.get(Strategy, sid)
    if not obj:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return obj

@router.post("", response_model=StrategyOut, status_code=status.HTTP_201_CREATED)
def create(payload: StrategyCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(Strategy).where(Strategy.name == payload.name))
    if existing:
        raise HTTPException(status_code=409, detail="Strategy name already exists")
    obj = Strategy(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("", response_model=List[StrategyOut])
def list_(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(None, description="Filter by name contains"),
    is_active: bool | None = Query(None),
):
    stmt = select(Strategy)
    if q:
        stmt = stmt.where(func.lower(Strategy.name).contains(q.lower()))
    if is_active is not None:
        stmt = stmt.where(Strategy.is_active == is_active)
    stmt = stmt.order_by(Strategy.created_at.desc()).limit(limit).offset(offset)
    return db.scalars(stmt).all()

@router.get("/{sid}", response_model=StrategyOut)
def get_one(sid: int, db: Session = Depends(get_db)):
    return _get(db, sid)

@router.patch("/{sid}", response_model=StrategyOut)
def update(sid: int, payload: StrategyUpdate, db: Session = Depends(get_db)):
    obj = _get(db, sid)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != obj.name:
        dup = db.scalar(select(Strategy).where(Strategy.name == data["name"]))
        if dup:
            raise HTTPException(status_code=409, detail="Strategy name already exists")
    for k, v in data.items():
        setattr(obj, k, v)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/{sid}", status_code=status.HTTP_204_NO_CONTENT)
def delete(sid: int, db: Session = Depends(get_db)):
    obj = _get(db, sid)
    db.delete(obj)
    db.commit()
    return None
