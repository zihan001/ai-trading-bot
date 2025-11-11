import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.symbol import Symbol
from app.repositories.symbol_repo import SymbolRepository


@pytest.mark.asyncio
class TestSymbolEndpoints:
    """Test symbol CRUD endpoints."""

    async def test_create_symbol_success(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test creating a new symbol."""
        response = await async_client.post("/symbols", json=sample_symbol_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["symbol"] == sample_symbol_data["symbol"]
        assert data["name"] == sample_symbol_data["name"]
        assert data["active"] == sample_symbol_data["active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_symbol_duplicate(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test that duplicate symbols are rejected."""
        # Create first symbol
        await async_client.post("/symbols", json=sample_symbol_data)
        
        # Try to create duplicate
        response = await async_client.post("/symbols", json=sample_symbol_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_symbol_invalid_data(self, async_client: AsyncClient):
        """Test creating symbol with invalid data."""
        invalid_data = {
            "symbol": "",  # Empty symbol should fail validation
            "active": "not_a_boolean"
        }
        
        response = await async_client.post("/symbols", json=invalid_data)
        assert response.status_code == 422

    async def test_get_symbol_success(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test retrieving a symbol by ID."""
        # Create symbol
        create_response = await async_client.post("/symbols", json=sample_symbol_data)
        symbol_id = create_response.json()["id"]
        
        # Get symbol
        response = await async_client.get(f"/symbols/{symbol_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == symbol_id
        assert data["symbol"] == sample_symbol_data["symbol"]

    async def test_get_symbol_not_found(self, async_client: AsyncClient):
        """Test retrieving a non-existent symbol."""
        response = await async_client.get("/symbols/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_list_symbols_empty(self, async_client: AsyncClient):
        """Test listing symbols when none exist."""
        response = await async_client.get("/symbols")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["limit"] == 50
        assert data["offset"] == 0

    async def test_list_symbols_with_data(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test listing symbols with data."""
        # Create multiple symbols
        symbols = [
            {**sample_symbol_data, "symbol": f"SYM{i}"}
            for i in range(3)
        ]
        
        for symbol in symbols:
            await async_client.post("/symbols", json=symbol)
        
        # List all
        response = await async_client.get("/symbols")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_symbols_pagination(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test symbol list pagination."""
        # Create 5 symbols
        for i in range(5):
            await async_client.post(
                "/symbols",
                json={**sample_symbol_data, "symbol": f"SYMB{i}"}
            )
        
        # Get first page
        response = await async_client.get("/symbols?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        
        # Get second page
        response = await async_client.get("/symbols?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    async def test_list_symbols_filter_by_symbol(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test filtering symbols by exact symbol."""
        target_symbol = "TSLA"
        
        # Create symbols
        await async_client.post("/symbols", json=sample_symbol_data)
        await async_client.post(
            "/symbols",
            json={**sample_symbol_data, "symbol": target_symbol}
        )
        
        # Filter by symbol
        response = await async_client.get(f"/symbols?symbol={target_symbol}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["symbol"] == target_symbol

    async def test_list_symbols_filter_by_active(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test filtering symbols by active status."""
        # Create active and inactive symbols
        await async_client.post("/symbols", json={**sample_symbol_data, "active": True})
        await async_client.post(
            "/symbols",
            json={**sample_symbol_data, "symbol": "INACTIVE", "active": False}
        )
        
        # Filter by active
        response = await async_client.get("/symbols?active=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["active"] is True

    async def test_list_symbols_search(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test searching symbols by symbol or name."""
        # Create symbols with different symbols/names
        await async_client.post(
            "/symbols",
            json={**sample_symbol_data, "symbol": "AAPL", "name": "Apple Inc."}
        )
        await async_client.post(
            "/symbols",
            json={
                **sample_symbol_data,
                "symbol": "MSFT",
                "name": "Microsoft with Apple reference"
            }
        )
        
        # Search for "apple"
        response = await async_client.get("/symbols?search=apple")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Matches both symbol and name

    async def test_list_symbols_ordering(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test symbol list ordering."""
        # Create symbols with different symbols
        symbols = ["AAPL", "MSFT", "GOOGL"]
        for sym in symbols:
            await async_client.post(
                "/symbols",
                json={**sample_symbol_data, "symbol": sym}
            )
        
        # Order by symbol ascending (default)
        response = await async_client.get("/symbols?order_by=symbol&order_dir=asc")
        assert response.status_code == 200
        data = response.json()
        result_symbols = [item["symbol"] for item in data["items"]]
        assert result_symbols == sorted(symbols)
        
        # Order by symbol descending
        response = await async_client.get("/symbols?order_by=symbol&order_dir=desc")
        assert response.status_code == 200
        data = response.json()
        result_symbols = [item["symbol"] for item in data["items"]]
        assert result_symbols == sorted(symbols, reverse=True)

    async def test_update_symbol_success(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test updating a symbol."""
        # Create symbol
        create_response = await async_client.post("/symbols", json=sample_symbol_data)
        symbol_id = create_response.json()["id"]
        
        # Update symbol
        update_data = {
            "name": "Updated Company Name",
            "active": False
        }
        response = await async_client.patch(f"/symbols/{symbol_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["active"] == update_data["active"]
        assert data["symbol"] == sample_symbol_data["symbol"]  # Unchanged

    async def test_update_symbol_partial(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test partial update of symbol."""
        # Create symbol
        create_response = await async_client.post("/symbols", json=sample_symbol_data)
        symbol_id = create_response.json()["id"]
        original_symbol = create_response.json()["symbol"]
        
        # Partial update (only active)
        response = await async_client.patch(
            f"/symbols/{symbol_id}",
            json={"active": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
        assert data["symbol"] == original_symbol  # Unchanged

    async def test_update_symbol_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent symbol."""
        response = await async_client.patch(
            "/symbols/99999",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404

    async def test_update_symbol_duplicate(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test updating symbol to a duplicate symbol."""
        # Create two symbols
        await async_client.post("/symbols", json=sample_symbol_data)
        response2 = await async_client.post(
            "/symbols",
            json={**sample_symbol_data, "symbol": "MSFT"}
        )
        symbol2_id = response2.json()["id"]
        
        # Try to update symbol2 to have the same symbol as symbol1
        response = await async_client.patch(
            f"/symbols/{symbol2_id}",
            json={"symbol": sample_symbol_data["symbol"]}
        )
        
        assert response.status_code == 409

    async def test_delete_symbol_success(
        self, async_client: AsyncClient, sample_symbol_data: dict
    ):
        """Test deleting a symbol."""
        # Create symbol
        create_response = await async_client.post("/symbols", json=sample_symbol_data)
        symbol_id = create_response.json()["id"]
        
        # Delete symbol
        response = await async_client.delete(f"/symbols/{symbol_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await async_client.get(f"/symbols/{symbol_id}")
        assert get_response.status_code == 404

    async def test_delete_symbol_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent symbol."""
        response = await async_client.delete("/symbols/99999")
        
        assert response.status_code == 404


class TestSymbolRepository:
    """Test symbol repository methods directly."""

    def test_create_symbol(self, db: Session, sample_symbol_data: dict):
        """Test creating a symbol via repository."""
        from app.schemas.symbol import SymbolCreate
        
        repo = SymbolRepository(db)
        symbol = repo.create(SymbolCreate(**sample_symbol_data))
        
        assert symbol.id is not None
        assert symbol.symbol == sample_symbol_data["symbol"]
        assert symbol.active == sample_symbol_data["active"]

    def test_create_duplicate_raises_error(self, db: Session, sample_symbol_data: dict):
        """Test that creating duplicate symbol raises ValueError."""
        from app.schemas.symbol import SymbolCreate
        
        repo = SymbolRepository(db)
        repo.create(SymbolCreate(**sample_symbol_data))
        
        with pytest.raises(ValueError, match="already exists"):
            repo.create(SymbolCreate(**sample_symbol_data))

    def test_get_symbol(self, db: Session, sample_symbol_data: dict):
        """Test retrieving a symbol by ID."""
        from app.schemas.symbol import SymbolCreate
        
        repo = SymbolRepository(db)
        created = repo.create(SymbolCreate(**sample_symbol_data))
        
        retrieved = repo.get(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.symbol == created.symbol

    def test_get_nonexistent_returns_none(self, db: Session):
        """Test that getting non-existent symbol returns None."""
        repo = SymbolRepository(db)
        result = repo.get(99999)
        
        assert result is None

    def test_list_and_count(self, db: Session, sample_symbol_data: dict):
        """Test listing symbols with count."""
        from app.schemas.symbol import SymbolCreate, SymbolQuery
        
        repo = SymbolRepository(db)
        
        # Create multiple symbols
        for i in range(3):
            repo.create(
                SymbolCreate(**{**sample_symbol_data, "symbol": f"SYM{i}"})
            )
        
        # List all
        query = SymbolQuery()
        rows, total = repo.list_and_count(query)
        
        assert total == 3
        assert len(rows) == 3

    def test_update_symbol(self, db: Session, sample_symbol_data: dict):
        """Test updating a symbol."""
        from app.schemas.symbol import SymbolCreate, SymbolUpdate
        
        repo = SymbolRepository(db)
        symbol = repo.create(SymbolCreate(**sample_symbol_data))
        
        # Update
        update = SymbolUpdate(name="Updated Name", active=False)
        updated = repo.update(symbol, update)
        
        assert updated.name == "Updated Name"
        assert updated.active is False

    def test_delete_symbol(self, db: Session, sample_symbol_data: dict):
        """Test deleting a symbol."""
        from app.schemas.symbol import SymbolCreate
        
        repo = SymbolRepository(db)
        symbol = repo.create(SymbolCreate(**sample_symbol_data))
        symbol_id = symbol.id
        
        # Delete
        repo.delete(symbol)
        
        # Verify deletion
        assert repo.get(symbol_id) is None