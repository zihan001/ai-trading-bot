from __future__ import annotations
from sqlalchemy.orm import Session

from app.models.symbol import Symbol
from app.schemas.symbol import SymbolCreate, SymbolUpdate, SymbolQuery
from app.repositories.base_repo import BaseRepository


class SymbolRepository(BaseRepository[Symbol, SymbolCreate, SymbolUpdate, SymbolQuery]):
    def __init__(self, db: Session):
        super().__init__(Symbol, db)

    def _apply_filters(self, stmt, q: SymbolQuery):
        """Apply symbol-specific filters."""
        if q.symbol:
            stmt = stmt.where(Symbol.symbol == q.symbol)
        if q.active is not None:
            stmt = stmt.where(Symbol.active == q.active)
        if q.search:
            like = f"%{q.search}%"
            stmt = stmt.where(
                (Symbol.symbol.ilike(like)) | (Symbol.name.ilike(like))
            )
        return stmt

    def create(self, payload: SymbolCreate) -> Symbol:
        """Create a new symbol."""
        return super().create(payload, error_msg="Symbol already exists")

    def update(self, symbol: Symbol, patch: SymbolUpdate) -> Symbol:
        """Update a symbol."""
        return super().update(symbol, patch, error_msg="Symbol already exists")