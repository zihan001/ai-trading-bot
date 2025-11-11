from __future__ import annotations
import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import String, Numeric, Enum, Boolean, DateTime, Text, UniqueConstraint, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db import Base


class OrderSide(str, enum.Enum):
    buy = "buy"
    sell = "sell"


class OrderType(str, enum.Enum):
    market = "market"
    limit = "limit"
    stop = "stop"
    stop_limit = "stop_limit"


class TimeInForce(str, enum.Enum):
    day = "day"
    gtc = "gtc"
    fok = "fok"
    ioc = "ioc"


class QuantityType(str, enum.Enum):
    units = "units"
    notional = "notional"


class PositionEffect(str, enum.Enum):
    open = "open"
    close = "close"
    auto = "auto"


class OrderStatus(str, enum.Enum):
    new = "new"
    pending_broker = "pending_broker"
    partially_filled = "partially_filled"
    filled = "filled"
    canceled = "canceled"
    rejected = "rejected"
    expired = "expired"


class Broker(str, enum.Enum):
    paper = "paper"
    alpaca = "alpaca"
    binance = "binance"
    ibkr = "ibkr"


class Order(Base):
    __tablename__ = "orders"
    
    __table_args__ = (
        UniqueConstraint("account_id", "client_order_id", name="uq_orders_account_client_order_id"),
        Index("ix_orders_created_symbol_status", "created_at", "symbol_id", "status"),
        Index("ix_orders_broker_broker_order_id", "broker", "broker_order_id"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    symbol_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    strategy_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    # Order details
    side: Mapped[OrderSide] = mapped_column(Enum(OrderSide, native_enum=False), nullable=False)
    type: Mapped[OrderType] = mapped_column(Enum(OrderType, native_enum=False), nullable=False)
    time_in_force: Mapped[TimeInForce] = mapped_column(
        Enum(TimeInForce, native_enum=False), 
        nullable=False, 
        default=TimeInForce.day
    )
    
    # Quantities and prices
    quantity: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False)
    quantity_type: Mapped[QuantityType] = mapped_column(
        Enum(QuantityType, native_enum=False), 
        nullable=False, 
        default=QuantityType.units
    )
    price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    
    # Execution details
    reduce_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    position_effect: Mapped[PositionEffect] = mapped_column(
        Enum(PositionEffect, native_enum=False), 
        nullable=False, 
        default=PositionEffect.auto
    )
    
    # Status tracking
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False), 
        nullable=False, 
        default=OrderStatus.new
    )
    average_fill_price: Mapped[Decimal | None] = mapped_column(Numeric(28, 10), nullable=True)
    filled_quantity: Mapped[Decimal] = mapped_column(Numeric(28, 10), nullable=False, default=Decimal("0"))
    
    # Broker details
    broker: Mapped[Broker] = mapped_column(
        Enum(Broker, native_enum=False), 
        nullable=False, 
        default=Broker.paper
    )
    broker_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    paper: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    
    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    placed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
