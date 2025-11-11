from __future__ import annotations
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate, AssetQuery
from app.repositories.base_repo import BaseRepository


class AssetRepository(BaseRepository[Asset, AssetCreate, AssetUpdate, AssetQuery]):
    def __init__(self, db: Session):
        super().__init__(Asset, db)

    def _apply_filters(self, stmt, q: AssetQuery):
        """Apply asset-specific filters."""
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
        return stmt

    def create(self, payload: AssetCreate) -> Asset:
        """Create a new asset."""
        return super().create(payload, error_msg="Asset with this exchange+symbol already exists")

    def update(self, asset: Asset, patch: AssetUpdate) -> Asset:
        """Update an asset."""
        return super().update(asset, patch, error_msg="Asset with this exchange+symbol already exists")
