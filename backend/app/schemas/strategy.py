from datetime import datetime
from pydantic import BaseModel, Field

class StrategyBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    is_active: bool = True

class StrategyCreate(StrategyBase):
    pass

class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None

class StrategyOut(StrategyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
