from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.symbol import SymbolCreate, SymbolRead, SymbolUpdate, SymbolQuery
from app.repositories.symbol_repo import SymbolRepository

router = APIRouter(prefix="/symbols", tags=["symbols"])


@router.post("", response_model=SymbolRead, status_code=status.HTTP_201_CREATED)
def create_symbol(payload: SymbolCreate, db: Session = Depends(get_db)):
    """Create a new trading symbol."""
    repo = SymbolRepository(db)
    try:
        return repo.create(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=dict)
def list_symbols(
    symbol: str | None = None,
    active: bool | None = None,
    search: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query("symbol", pattern="^(created_at|updated_at|symbol|name|active)$"),
    order_dir: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List symbols with optional filtering and pagination.
    
    - **symbol**: Filter by exact symbol match
    - **active**: Filter by active status
    - **search**: Search in symbol or name (case-insensitive)
    - **limit**: Maximum number of results (1-200, default 50)
    - **offset**: Number of results to skip (default 0)
    - **order_by**: Field to sort by (default: symbol)
    - **order_dir**: Sort direction: asc or desc (default: asc)
    """
    repo = SymbolRepository(db)
    q = SymbolQuery(
        symbol=symbol,
        active=active,
        search=search,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )
    rows, total = repo.list_and_count(q)
    return {
        "items": [SymbolRead.model_validate(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{symbol_id}", response_model=SymbolRead)
def get_symbol(symbol_id: int, db: Session = Depends(get_db)):
    """Get a single symbol by ID."""
    repo = SymbolRepository(db)
    entity = repo.get(symbol_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not found")
    return entity


@router.patch("/{symbol_id}", response_model=SymbolRead)
def update_symbol(symbol_id: int, patch: SymbolUpdate, db: Session = Depends(get_db)):
    """Update a symbol (partial update)."""
    repo = SymbolRepository(db)
    entity = repo.get(symbol_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not found")
    try:
        return repo.update(entity, patch)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{symbol_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_symbol(symbol_id: int, db: Session = Depends(get_db)):
    """Delete a symbol."""
    repo = SymbolRepository(db)
    entity = repo.get(symbol_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Symbol not found")
    repo.delete(entity)
    return None