from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

class Symbol(Base):
    __tablename__ = "symbols"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(120))
    active: Mapped[bool] = mapped_column(default=True)