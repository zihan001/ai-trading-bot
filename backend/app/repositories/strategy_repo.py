from __future__ import annotations
from typing import Sequence, Tuple
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate, StrategyQuery


class StrategyRepository:
    def __init__(self, db: Session):
        self.db = db

    def _order_clause(self, field: str, direction: str):
        col = getattr(Strategy, field)
        return asc(col) if direction == "asc" else desc(col)

    def create(self, payload: StrategyCreate) -> Strategy:
        entity = Strategy(**payload.model_dump())
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Strategy with this name already exists") from e
        self.db.refresh(entity)
        return entity

    def get(self, strategy_id: int) -> Strategy | None:
        return self.db.get(Strategy, strategy_id)

    def list_and_count(self, q: StrategyQuery) -> Tuple[Sequence[Strategy], int]:
        stmt = select(Strategy)
        
        if q.name:
            stmt = stmt.where(Strategy.name == q.name)
        if q.is_active is not None:
            stmt = stmt.where(Strategy.is_active == q.is_active)
        if q.search:
            like = f"%{q.search}%"
            stmt = stmt.where(
                (Strategy.name.ilike(like)) | (Strategy.description.ilike(like))
            )

        order = self._order_clause(q.order_by or "created_at", q.order_dir or "desc")
        stmt = stmt.order_by(order).offset(q.offset).limit(q.limit)

        rows = self.db.execute(stmt).scalars().all()

        # Count query with same filters
        count_stmt = select(func.count()).select_from(Strategy)
        if q.name:
            count_stmt = count_stmt.where(Strategy.name == q.name)
        if q.is_active is not None:
            count_stmt = count_stmt.where(Strategy.is_active == q.is_active)
        if q.search:
            like = f"%{q.search}%"
            count_stmt = count_stmt.where(
                (Strategy.name.ilike(like)) | (Strategy.description.ilike(like))
            )

        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def update(self, strategy: Strategy, patch: StrategyUpdate) -> Strategy:
        data = patch.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(strategy, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Strategy with this name already exists") from e
        self.db.refresh(strategy)
        return strategy

    def delete(self, strategy: Strategy) -> None:
        self.db.delete(strategy)
        self.db.commit()