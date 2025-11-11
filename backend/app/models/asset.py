from __future__ import annotations
import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Enum, Boolean, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, declarative_mixin
from sqlalchemy.dialects.postgresql import UUID
from app.db import Base 

class AssetType(str, enum.Enum):
    equity = "equity"
    etf = "etf"
    forex = "forex"
    crypto = "crypto"
    future = "future"
    option = "option"
    bond = "bond"
    other = "other"

@declarative_mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)               # e.g. AAPL, BTC-USD, EURUSD
    name: Mapped[str] = mapped_column(String(200), nullable=False)                # human-friendly
    exchange: Mapped[str] = mapped_column(String(50), nullable=False)             # e.g. NASDAQ, NYSE, BINANCE, OANDA
    asset_type: Mapped[AssetType] = mapped_column(Enum(AssetType, native_enum=False), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta_json: Mapped[str | None] = mapped_column(String, nullable=True)          # optional: JSON as string if SQLite; use JSON if Postgres

    __table_args__ = (
        UniqueConstraint("exchange", "symbol", name="uq_assets_exchange_symbol"),
        Index("ix_assets_symbol", "symbol"),
        Index("ix_assets_exchange", "exchange"),
        Index("ix_assets_type", "asset_type"),
        Index("ix_assets_active", "is_active"),
    )