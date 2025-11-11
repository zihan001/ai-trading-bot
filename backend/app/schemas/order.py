from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

# Import enums from model
from app.models.order import (
    OrderSide, OrderType, TimeInForce, QuantityType, 
    PositionEffect, OrderStatus, Broker
)


class OrderBase(BaseModel):
    symbol_id: UUID
    strategy_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    side: OrderSide
    type: OrderType
    time_in_force: TimeInForce = TimeInForce.day
    quantity: Annotated[Decimal, Field(gt=0)]
    quantity_type: QuantityType = QuantityType.units
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    reduce_only: bool = False
    position_effect: PositionEffect = PositionEffect.auto
    broker: Broker = Broker.paper
    client_order_id: Optional[str] = Field(None, max_length=128)
    paper: bool = True
    notes: Optional[str] = None

    @field_validator("quantity", "price", "stop_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert strings to Decimal for validation."""
        if v is None:
            return v
        if isinstance(v, str):
            return Decimal(v)
        return v

    @model_validator(mode="after")
    def validate_order_type_requirements(self):
        """Validate price/stop_price requirements based on order type."""
        if self.type == OrderType.limit and self.price is None:
            raise ValueError("price is required for limit orders")
        
        if self.type == OrderType.stop and self.stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        
        if self.type == OrderType.stop_limit:
            if self.price is None:
                raise ValueError("price is required for stop_limit orders")
            if self.stop_price is None:
                raise ValueError("stop_price is required for stop_limit orders")
        
        return self

    @model_validator(mode="after")
    def validate_time_in_force(self):
        """Validate time_in_force based on order type."""
        if self.time_in_force in (TimeInForce.fok, TimeInForce.ioc):
            if self.type not in (OrderType.market, OrderType.limit):
                raise ValueError(f"time_in_force {self.time_in_force.value} only valid for market or limit orders")
        
        return self


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    """Only allow updating specific fields, and only in certain states."""
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    time_in_force: Optional[TimeInForce] = None
    notes: Optional[str] = None
    reduce_only: Optional[bool] = None

    @field_validator("price", "stop_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return Decimal(v)
        return v


class OrderRead(OrderBase):
    id: UUID
    status: OrderStatus
    average_fill_price: Optional[Decimal] = None
    filled_quantity: Decimal
    broker_order_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    placed_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OrderQuery(BaseModel):
    """Query parameters for listing orders."""
    symbol_id: Optional[UUID] = None
    strategy_id: Optional[UUID] = None
    status: Optional[OrderStatus] = None
    side: Optional[OrderSide] = None
    broker: Optional[Broker] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    order_by: Optional[Literal[
        "created_at", "updated_at", "symbol_id", "status", "side", "quantity"
    ]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"