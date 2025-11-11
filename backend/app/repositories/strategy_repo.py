from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyQuery
from app.repositories.base_repo import BaseRepository


class StrategyRepository(BaseRepository[Strategy, StrategyCreate, StrategyUpdate, StrategyQuery]):
    def __init__(self, db: Session):
        super().__init__(Strategy, db)

    def _apply_filters(self, stmt, q: StrategyQuery):
        """Apply strategy-specific filters."""
        if q.name:
            stmt = stmt.where(Strategy.name == q.name)
        if q.is_active is not None:
            stmt = stmt.where(Strategy.is_active == q.is_active)
        if q.search:
            like = f"%{q.search}%"
            stmt = stmt.where(
                (Strategy.name.ilike(like)) | (Strategy.description.ilike(like))
            )
        return stmt

    def create(self, payload: StrategyCreate) -> Strategy:
        """Create a new strategy."""
        return super().create(payload, error_msg="Strategy with this name already exists")

    def update(self, strategy: Strategy, patch: StrategyUpdate) -> Strategy:
        """Update a strategy."""
        return super().update(strategy, patch, error_msg="Strategy with this name already exists")