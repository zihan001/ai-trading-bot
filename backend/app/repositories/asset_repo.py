from __future__ import annotations
from typing import Sequence, Tuple
from uuid import UUID
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.asset import Asset, AssetType
from app.schemas.asset import AssetCreate, AssetUpdate, AssetQuery

class AssetRepository:
    def __init__(self, db: Session):
        self.db = db

    def _order_clause(self, field: str, direction: str):
        col = getattr(Asset, field)
        return asc(col) if direction == "asc" else desc(col)

    def create(self, payload: AssetCreate) -> Asset:
        entity = Asset(**payload.model_dump())
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            # Likely unique constraint on (exchange, symbol)
            raise ValueError("Asset with this exchange+symbol already exists") from e
        self.db.refresh(entity)
        return entity

    def get(self, asset_id: UUID) -> Asset | None:
        return self.db.get(Asset, asset_id)

    def list_and_count(self, q: AssetQuery) -> Tuple[Sequence[Asset], int]:
        stmt = select(Asset)
        if q.symbol:
            stmt = stmt.where(Asset.symbol == q.symbol)
        if q.exchange:
            stmt = stmt.where(Asset.exchange == q.exchange)
        if q.asset_type:
            stmt = stmt.where(Asset.asset_type == q.asset_type)
        if q.is_active is not None:
            stmt = stmt.where(Asset.is_active == q.is_active)
        if q.search:
            like = f"%{q.search}%"
            stmt = stmt.where((Asset.symbol.ilike(like)) | (Asset.name.ilike(like)))

        order = self._order_clause(q.order_by or "symbol", q.order_dir or "asc")
        stmt = stmt.order_by(order).offset(q.offset).limit(q.limit)

        rows = self.db.execute(stmt).scalars().all()

        count_stmt = select(func.count()).select_from(Asset)
        # mirror filters for count
        if q.symbol:
            count_stmt = count_stmt.where(Asset.symbol == q.symbol)
        if q.exchange:
            count_stmt = count_stmt.where(Asset.exchange == q.exchange)
        if q.asset_type:
            count_stmt = count_stmt.where(Asset.asset_type == q.asset_type)
        if q.is_active is not None:
            count_stmt = count_stmt.where(Asset.is_active == q.is_active)
        if q.search:
            like = f"%{q.search}%"
            count_stmt = count_stmt.where((Asset.symbol.ilike(like)) | (Asset.name.ilike(like)))

        total = self.db.execute(count_stmt).scalar_one()
        return rows, total

    def update(self, asset: Asset, patch: AssetUpdate) -> Asset:
        data = patch.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(asset, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError("Asset with this exchange+symbol already exists") from e
        self.db.refresh(asset)
        return asset

    def delete(self, asset: Asset) -> None:
        self.db.delete(asset)
        self.db.commit()
