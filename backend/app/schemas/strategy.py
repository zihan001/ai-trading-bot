from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field

class StrategyBase(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    description: Optional[str] = None
    is_active: bool = True

class StrategyCreate(StrategyBase):
    pass

class StrategyUpdate(BaseModel):
    # All optional fields for PATCH semantics
    name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class StrategyRead(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

class StrategyQuery(BaseModel):
    # For list endpoint filtering
    name: Optional[str] = Field(None, description="Exact name match")
    is_active: Optional[bool] = None
    search: Optional[str] = Field(None, description="ILIKE on name or description")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    order_by: Optional[Literal["created_at", "updated_at", "name", "is_active"]] = "created_at"
    order_dir: Optional[Literal["asc", "desc"]] = "desc"
