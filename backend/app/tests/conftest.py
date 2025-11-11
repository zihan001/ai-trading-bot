import os
import sys
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient, ASGITransport

# Add parent directory to Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["POSTGRES_HOST"] = "localhost"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["JWT_SECRET"] = "test_secret"
os.environ["ENV"] = "test"

from app.main import app
from app.db import Base
from app.api.deps import get_db

# Create in-memory SQLite engine for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override the get_db dependency for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture(scope="function")
async def async_client(db: Session) -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing FastAPI endpoints."""
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_strategy_data():
    """Sample strategy data for tests."""
    return {
        "name": "Momentum Strategy",
        "description": "A simple momentum-based trading strategy",
        "is_active": True
    }


@pytest.fixture
def sample_asset_data():
    """Sample asset data for tests."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "asset_type": "equity",
        "currency": "USD",
        "is_active": True
    }


@pytest.fixture
def sample_symbol_data():
    """Sample symbol data for tests."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "active": True
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for tests."""
    import uuid
    return {
        "symbol_id": str(uuid.uuid4()),
        "side": "buy",
        "type": "limit",
        "quantity": "100",
        "price": "150.50",
        "time_in_force": "day",
        "paper": True
    }