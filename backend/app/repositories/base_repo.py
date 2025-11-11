from __future__ import annotations
from typing import Generic, TypeVar, Type, Sequence, Tuple, Any
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel

# Type variables for generic repository
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
QuerySchemaType = TypeVar("QuerySchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType, QuerySchemaType]):
    """Base repository with common CRUD operations."""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def _order_clause(self, field: str, direction: str):
        """Build order clause for queries."""
        col = getattr(self.model, field)
        return asc(col) if direction == "asc" else desc(col)
    
    def _apply_filters(self, stmt, q: QuerySchemaType):
        """Apply query filters to statement. Override in subclasses for specific filtering."""
        return stmt
    
    def create(self, payload: CreateSchemaType, error_msg: str = "Entity already exists") -> ModelType:
        """Create a new entity."""
        entity = self.model(**payload.model_dump())
        self.db.add(entity)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(error_msg) from e
        self.db.refresh(entity)
        return entity
    
    def get(self, entity_id: Any) -> ModelType | None:
        """Get entity by ID."""
        return self.db.get(self.model, entity_id)
    
    def list_and_count(self, q: QuerySchemaType) -> Tuple[Sequence[ModelType], int]:
        """List entities with filtering and count total."""
        stmt = select(self.model)
        stmt = self._apply_filters(stmt, q)
        
        order_by = getattr(q, "order_by", None)
        order_dir = getattr(q, "order_dir", "asc")
        if order_by:
            order = self._order_clause(order_by, order_dir)
            stmt = stmt.order_by(order)
        
        limit = getattr(q, "limit", 50)
        offset = getattr(q, "offset", 0)
        stmt = stmt.offset(offset).limit(limit)
        
        rows = self.db.execute(stmt).scalars().all()
        
        # Count query with same filters
        count_stmt = select(func.count()).select_from(self.model)
        count_stmt = self._apply_filters(count_stmt, q)
        total = self.db.execute(count_stmt).scalar_one()
        
        return rows, total
    
    def update(self, entity: ModelType, patch: UpdateSchemaType, error_msg: str = "Update failed due to constraint violation") -> ModelType:
        """Update entity with partial data."""
        data = patch.model_dump(exclude_unset=True)
        for k, v in data.items():
            setattr(entity, k, v)
        try:
            self.db.commit()
        except IntegrityError as e:
            self.db.rollback()
            raise ValueError(error_msg) from e
        self.db.refresh(entity)
        return entity
    
    def delete(self, entity: ModelType) -> None:
        """Delete entity."""
        self.db.delete(entity)
        self.db.commit()
