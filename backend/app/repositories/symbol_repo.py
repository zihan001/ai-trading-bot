from __future__ import annotations
from typing import Sequence, Tuple
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.symbol import Symbol
from app.schemas.symbol import SymbolCreate, SymbolUpdate, SymbolQuery


class SymbolRepository:
    def __init__(self, db: Session):
        self.db = db

    def _order_clause(self, field: str, direction: str):
        col = getattr(Symbol, field)
        return asc(col) if direction == "asc" else desc(col)

    def create(self, payload: SymbolCreate) -> Symbol:
        entity = Symbol(**payload.model_dump())
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Symbol already exists") from e
        self.db.refresh(entity)
        return entity

    def get(self, symbol_id: int) -> Symbol | None:
        return self.db.get(Symbol, symbol_id)

    def list_and_count(self, q: SymbolQuery) -> Tuple[Sequence[Symbol], int]:
        stmt = select(Symbol)
        
        if q.symbol:
            stmt = stmt.where(Symbol.symbol == q.symbol)
        if q.active is not None:
            stmt = stmt.where(Symbol.active == q.active)
        if q.search:
            like = f"%{q.search}%"
            stmt = stmt.where(
                (Symbol.symbol.ilike(like)) | (Symbol.name.ilike(like))
            )

        order = self._order_clause(q.order_by or "symbol", q.order_dir or "asc")
        stmt = stmt.order_by(order).offset(q.offset).limit(q.limit)

        rows = self.db.execute(stmt).scalars().all()

        # Count query with same filters
        count_stmt = select(func.count()).select_from(Symbol)
        if q.symbol:
            count_stmt = count_stmt.where(Symbol.symbol == q.symbol)
        if q.active is not None:
            count_stmt = count_stmt.where(Symbol.active == q.active)
        if q.search:
            like = f"%{q.search}%"
            count_stmt = count_stmt.where(
                (Symbol.symbol.ilike(like)) | (Symbol.name.ilike(like))
            )

        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def update(self, symbol: Symbol, patch: SymbolUpdate) -> Symbol:
        data = patch.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(symbol, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Symbol already exists") from e
        self.db.refresh(symbol)
        return symbol

    def delete(self, symbol: Symbol) -> None:
        self.db.delete(symbol)
        self.db.commit()