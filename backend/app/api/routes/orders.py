from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.order import OrderCreate, OrderRead, OrderUpdate, OrderQuery
from app.repositories.order_repo import OrderRepository

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    Create a new order.
    
    Validates all business rules:
    - Order type requirements (price, stop_price)
    - Time in force restrictions
    - Idempotency via client_order_id
    """
    repo = OrderRepository(db)
    try:
        return repo.create(payload)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=dict)
def list_orders(
    symbol_id: UUID | None = None,
    strategy_id: UUID | None = None,
    status: str | None = None,
    side: str | None = None,
    broker: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    order_by: str = Query(
        "created_at", 
        pattern="^(created_at|updated_at|symbol_id|status|side|quantity)$"
    ),
    order_dir: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    """
    List orders with filtering and pagination.
    
    - **symbol_id**: Filter by symbol UUID
    - **strategy_id**: Filter by strategy UUID
    - **status**: Filter by order status
    - **side**: Filter by buy/sell
    - **broker**: Filter by broker
    - **created_from**: Filter orders created after this timestamp
    - **created_to**: Filter orders created before this timestamp
    - **limit**: Maximum number of results (1-200, default 50)
    - **offset**: Number of results to skip (default 0)
    - **order_by**: Field to sort by (default: created_at)
    - **order_dir**: Sort direction: asc or desc (default: desc)
    """
    repo = OrderRepository(db)
    
    # Convert string timestamps to datetime if provided
    from datetime import datetime
    created_from_dt = datetime.fromisoformat(created_from) if created_from else None
    created_to_dt = datetime.fromisoformat(created_to) if created_to else None
    
    q = OrderQuery(
        symbol_id=symbol_id,
        strategy_id=strategy_id,
        status=status,
        side=side,
        broker=broker,
        created_from=created_from_dt,
        created_to=created_to_dt,
        limit=limit,
        offset=offset,
        order_by=order_by,
        order_dir=order_dir,
    )
    rows, total = repo.list_and_count(q)
    return {
        "items": [OrderRead.model_validate(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get a single order by ID."""
    repo = OrderRepository(db)
    try:
        uuid_obj = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Invalid UUID format"
        )
    
    entity = repo.get(uuid_obj)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found"
        )
    return entity


@router.patch("/{order_id}", response_model=OrderRead)
def update_order(order_id: str, patch: OrderUpdate, db: Session = Depends(get_db)):
    """
    Update an order (partial update).
    
    Only allowed when order is in 'new' or 'pending_broker' status.
    
    Editable fields:
    - price
    - stop_price
    - time_in_force
    - notes
    - reduce_only
    
    Quantity cannot be changed after creation.
    """
    repo = OrderRepository(db)
    try:
        uuid_obj = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Invalid UUID format"
        )
    
    entity = repo.get(uuid_obj)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found"
        )
    
    try:
        return repo.update(entity, patch)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{order_id}", response_model=OrderRead)
def cancel_order(order_id: str, db: Session = Depends(get_db)):
    """
    Cancel an order (soft delete - sets status to canceled).
    
    Only allowed when order is in:
    - new
    - pending_broker
    - partially_filled
    
    Returns the updated order (idempotent operation).
    """
    repo = OrderRepository(db)
    try:
        uuid_obj = UUID(order_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail="Invalid UUID format"
        )
    
    entity = repo.get(uuid_obj)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Order not found"
        )
    
    try:
        return repo.cancel(entity)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))