from __future__ import annotations
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderQuery
from app.repositories.base_repo import BaseRepository


class OrderRepository(BaseRepository[Order, OrderCreate, OrderUpdate, OrderQuery]):
    def __init__(self, db: Session):
        super().__init__(Order, db)

    def _apply_filters(self, stmt, q: OrderQuery):
        """Apply order-specific filters."""
        if q.symbol_id:
            stmt = stmt.where(Order.symbol_id == q.symbol_id)
        if q.strategy_id:
            stmt = stmt.where(Order.strategy_id == q.strategy_id)
        if q.status:
            stmt = stmt.where(Order.status == q.status)
        if q.side:
            stmt = stmt.where(Order.side == q.side)
        if q.broker:
            stmt = stmt.where(Order.broker == q.broker)
        if q.created_from:
            stmt = stmt.where(Order.created_at >= q.created_from)
        if q.created_to:
            stmt = stmt.where(Order.created_at <= q.created_to)
        return stmt

    def create(self, payload: OrderCreate) -> Order:
        """Create a new order with idempotency support via client_order_id."""
        # Check for duplicate client_order_id if provided
        if payload.client_order_id and payload.account_id:
            existing = self.db.execute(
                select(Order).where(
                    Order.account_id == payload.account_id,
                    Order.client_order_id == payload.client_order_id
                )
            ).scalar_one_or_none()
            
            if existing:
                raise ValueError("Order with this client_order_id already exists for this account")
        
        return super().create(payload, error_msg="Order creation failed due to constraint violation")

    def update(self, order: Order, patch: OrderUpdate) -> Order:
        """Update order with validation for status and fields."""
        # Only allow updates in certain states
        if order.status not in (OrderStatus.new, OrderStatus.pending_broker):
            raise ValueError(f"Cannot update order in status: {order.status.value}")
        
        data = patch.model_dump(exclude_unset=True)
        
        # Don't allow changing quantity after creation
        if "quantity" in data:
            raise ValueError("Cannot change quantity after order creation")
        
        return super().update(order, patch, error_msg="Order update failed due to constraint violation")

    def cancel(self, order: Order) -> Order:
        """Cancel an order (sets status and timestamp)."""
        # Check if order can be canceled
        if order.status not in (
            OrderStatus.new, 
            OrderStatus.pending_broker, 
            OrderStatus.partially_filled
        ):
            raise ValueError(f"Cannot cancel order in status: {order.status.value}")
        
        order.status = OrderStatus.canceled
        order.canceled_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(order)
        return order