from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.strategy import StrategyCreate, StrategyRead, StrategyUpdate, StrategyQuery
from app.repositories.strategy_repo import StrategyRepository

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("", response_model=StrategyRead, status_code=status.HTTP_201_CREATED)
def create_strategy(payload: StrategyCreate, db: Session = Depends(get_db)):
    """Create a new strategy."""
    repo = StrategyRepository(db)
    try:
        return repo.create(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=dict)
def list_strategies(
    name: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query("created_at", pattern="^(created_at|updated_at|name|is_active)$"),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List strategies with optional filtering and pagination.

    - **name**: Filter by exact name match
    - **is_active**: Filter by active status
    - **search**: Search in name or description (case-insensitive)
    - **limit**: Maximum number of results (1-200, default 50)
    - **offset**: Number of results to skip (default 0)
    - **order_by**: Field to sort by (default: created_at)
    - **order_dir**: Sort direction: asc or desc (default: desc)
    """
    repo = StrategyRepository(db)
    q = StrategyQuery(
        name=name,
        is_active=is_active,
        search=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )
    rows, total = repo.list_and_count(q)
    return {
        "items": [StrategyRead.model_validate(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{strategy_id}", response_model=StrategyRead)
def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get a single strategy by ID."""
    repo = StrategyRepository(db)
    entity = repo.get(strategy_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    return entity


@router.patch("/{strategy_id}", response_model=StrategyRead)
def update_strategy(strategy_id: int, patch: StrategyUpdate, db: Session = Depends(get_db)):
    """Update a strategy (partial update)."""
    repo = StrategyRepository(db)
    entity = repo.get(strategy_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    try:
        return repo.update(entity, patch)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Delete a strategy."""
    repo = StrategyRepository(db)
    entity = repo.get(strategy_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found")
    repo.delete(entity)
    return None
