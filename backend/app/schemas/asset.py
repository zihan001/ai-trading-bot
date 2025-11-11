from __future__ import annotations
from datetime import datetime
from uuid import UUID
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field

AssetType = Literal["equity", "etf", "forex", "crypto", "future", "option", "bond", "other"]

class AssetBase(BaseModel):
    symbol: Annotated[str, Field(min_length=1, max_length=50)]
    name: Annotated[str, Field(min_length=1, max_length=200)]
    exchange: Annotated[str, Field(min_length=1, max_length=50)]
    asset_type: AssetType
    currency: Annotated[str, Field(min_length=3, max_length=10)] = "USD"
    is_active: bool = True
    meta_json: Optional[str] = None  # if you store JSON string or use dict with actual JSON column

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    # all optional fields for PATCH semantics
    symbol: Optional[Annotated[str, Field(min_length=1, max_length=50)]] = None
    name: Optional[Annotated[str, Field(min_length=1, max_length=200)]] = None
    exchange: Optional[Annotated[str, Field(min_length=1, max_length=50)]] = None
    asset_type: Optional[AssetType] = None
    currency: Optional[Annotated[str, Field(min_length=3, max_length=10)]] = None
    is_active: Optional[bool] = None
    meta_json: Optional[str] = None

class AssetRead(AssetBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class AssetQuery(BaseModel):
    # for list endpoint filtering
    symbol: Optional[str] = Field(None, description="Exact symbol match")
    exchange: Optional[str] = None
    asset_type: Optional[AssetType] = None
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, description="ILIKE on symbol or name")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    order_by: Optional[Literal["created_at","updated_at","symbol","exchange","asset_type","name"]] = "symbol"
    order_dir: Optional[Literal["asc","desc"]] = "asc"
