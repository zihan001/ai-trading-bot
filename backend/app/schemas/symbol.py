from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field


class SymbolBase(BaseModel):
    symbol: Annotated[str, Field(min_length=1, max_length=20)]
    name: Optional[str] = Field(None, max_length=120)
    active: bool = True


class SymbolCreate(SymbolBase):
    pass


class SymbolUpdate(BaseModel):
    # All optional fields for PATCH semantics
    symbol: Optional[Annotated[str, Field(min_length=1, max_length=20)]] = None
    name: Optional[str] = Field(None, max_length=120)
    active: Optional[bool] = None


class SymbolRead(SymbolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SymbolQuery(BaseModel):
    # For list endpoint filtering
    symbol: Optional[str] = Field(None, description="Exact symbol match")
    active: Optional[bool] = None
    search: Optional[str] = Field(None, description="ILIKE on symbol or name")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    order_by: Optional[Literal["created_at", "updated_at", "symbol", "name", "active"]] = "symbol"
    order_dir: Optional[Literal["asc", "desc"]] = "asc"