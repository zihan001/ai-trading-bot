import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.repositories.strategy_repo import StrategyRepository


@pytest.mark.asyncio
class TestStrategyEndpoints:
    """Test strategy CRUD endpoints."""

    async def test_create_strategy_success(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test creating a new strategy."""
        response = await async_client.post("/strategies", json=sample_strategy_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_strategy_data["name"]
        assert data["description"] == sample_strategy_data["description"]
        assert data["is_active"] == sample_strategy_data["is_active"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_strategy_duplicate_name(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test that duplicate strategy names are rejected."""
        # Create first strategy
        await async_client.post("/strategies", json=sample_strategy_data)
        
        # Try to create duplicate
        response = await async_client.post("/strategies", json=sample_strategy_data)
        
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_strategy_invalid_data(self, async_client: AsyncClient):
        """Test creating strategy with invalid data."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "is_active": "not_a_boolean"
        }
        
        response = await async_client.post("/strategies", json=invalid_data)
        assert response.status_code == 422

    async def test_get_strategy_success(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test retrieving a strategy by ID."""
        # Create strategy
        create_response = await async_client.post("/strategies", json=sample_strategy_data)
        strategy_id = create_response.json()["id"]
        
        # Get strategy
        response = await async_client.get(f"/strategies/{strategy_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == strategy_id
        assert data["name"] == sample_strategy_data["name"]

    async def test_get_strategy_not_found(self, async_client: AsyncClient):
        """Test retrieving a non-existent strategy."""
        response = await async_client.get("/strategies/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_list_strategies_empty(self, async_client: AsyncClient):
        """Test listing strategies when none exist."""
        response = await async_client.get("/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["limit"] == 50
        assert data["offset"] == 0

    async def test_list_strategies_with_data(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test listing strategies with data."""
        # Create multiple strategies
        strategies = [
            {**sample_strategy_data, "name": f"Strategy {i}"}
            for i in range(3)
        ]
        
        for strategy in strategies:
            await async_client.post("/strategies", json=strategy)
        
        # List all
        response = await async_client.get("/strategies")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_strategies_pagination(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test strategy list pagination."""
        # Create 5 strategies
        for i in range(5):
            await async_client.post(
                "/strategies",
                json={**sample_strategy_data, "name": f"Strategy {i}"}
            )
        
        # Get first page
        response = await async_client.get("/strategies?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        
        # Get second page
        response = await async_client.get("/strategies?limit=2&offset=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    async def test_list_strategies_filter_by_name(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test filtering strategies by exact name."""
        target_name = "Unique Strategy Name"
        
        # Create strategies
        await async_client.post("/strategies", json=sample_strategy_data)
        await async_client.post(
            "/strategies",
            json={**sample_strategy_data, "name": target_name}
        )
        
        # Filter by name
        response = await async_client.get(f"/strategies?name={target_name}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == target_name

    async def test_list_strategies_filter_by_active(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test filtering strategies by active status."""
        # Create active and inactive strategies
        await async_client.post("/strategies", json={**sample_strategy_data, "is_active": True})
        await async_client.post(
            "/strategies",
            json={**sample_strategy_data, "name": "Inactive Strategy", "is_active": False}
        )
        
        # Filter by active
        response = await async_client.get("/strategies?is_active=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_active"] is True

    async def test_list_strategies_search(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test searching strategies by name or description."""
        # Create strategies with different names/descriptions
        await async_client.post(
            "/strategies",
            json={**sample_strategy_data, "name": "Momentum Strategy"}
        )
        await async_client.post(
            "/strategies",
            json={
                **sample_strategy_data,
                "name": "Mean Reversion",
                "description": "Uses momentum indicators"
            }
        )
        
        # Search for "momentum"
        response = await async_client.get("/strategies?search=momentum")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Matches both name and description

    async def test_list_strategies_ordering(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test strategy list ordering."""
        # Create strategies with different names
        names = ["Alpha", "Beta", "Gamma"]
        for name in names:
            await async_client.post(
                "/strategies",
                json={**sample_strategy_data, "name": name}
            )
        
        # Order by name ascending
        response = await async_client.get("/strategies?order_by=name&order_dir=asc")
        assert response.status_code == 200
        data = response.json()
        result_names = [item["name"] for item in data["items"]]
        assert result_names == sorted(names)
        
        # Order by name descending
        response = await async_client.get("/strategies?order_by=name&order_dir=desc")
        assert response.status_code == 200
        data = response.json()
        result_names = [item["name"] for item in data["items"]]
        assert result_names == sorted(names, reverse=True)

    async def test_update_strategy_success(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test updating a strategy."""
        # Create strategy
        create_response = await async_client.post("/strategies", json=sample_strategy_data)
        strategy_id = create_response.json()["id"]
        
        # Update strategy
        update_data = {
            "name": "Updated Strategy Name",
            "is_active": False
        }
        response = await async_client.patch(f"/strategies/{strategy_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["is_active"] == update_data["is_active"]
        assert data["description"] == sample_strategy_data["description"]  # Unchanged

    async def test_update_strategy_partial(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test partial update of strategy."""
        # Create strategy
        create_response = await async_client.post("/strategies", json=sample_strategy_data)
        strategy_id = create_response.json()["id"]
        original_name = create_response.json()["name"]
        
        # Partial update (only is_active)
        response = await async_client.patch(
            f"/strategies/{strategy_id}",
            json={"is_active": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is False
        assert data["name"] == original_name  # Unchanged

    async def test_update_strategy_not_found(self, async_client: AsyncClient):
        """Test updating a non-existent strategy."""
        response = await async_client.patch(
            "/strategies/99999",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404

    async def test_update_strategy_duplicate_name(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test updating strategy to a duplicate name."""
        # Create two strategies
        await async_client.post("/strategies", json=sample_strategy_data)
        response2 = await async_client.post(
            "/strategies",
            json={**sample_strategy_data, "name": "Another Strategy"}
        )
        strategy2_id = response2.json()["id"]
        
        # Try to update strategy2 to have the same name as strategy1
        response = await async_client.patch(
            f"/strategies/{strategy2_id}",
            json={"name": sample_strategy_data["name"]}
        )
        
        assert response.status_code == 409

    async def test_delete_strategy_success(
        self, async_client: AsyncClient, sample_strategy_data: dict
    ):
        """Test deleting a strategy."""
        # Create strategy
        create_response = await async_client.post("/strategies", json=sample_strategy_data)
        strategy_id = create_response.json()["id"]
        
        # Delete strategy
        response = await async_client.delete(f"/strategies/{strategy_id}")
        
        assert response.status_code == 204
        
        # Verify deletion
        get_response = await async_client.get(f"/strategies/{strategy_id}")
        assert get_response.status_code == 404

    async def test_delete_strategy_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent strategy."""
        response = await async_client.delete("/strategies/99999")
        
        assert response.status_code == 404


class TestStrategyRepository:
    """Test strategy repository methods directly."""

    def test_create_strategy(self, db: Session, sample_strategy_data: dict):
        """Test creating a strategy via repository."""
        from app.schemas.strategy import StrategyCreate
        
        repo = StrategyRepository(db)
        strategy = repo.create(StrategyCreate(**sample_strategy_data))
        
        assert strategy.id is not None
        assert strategy.name == sample_strategy_data["name"]
        assert strategy.is_active == sample_strategy_data["is_active"]

    def test_create_duplicate_raises_error(self, db: Session, sample_strategy_data: dict):
        """Test that creating duplicate strategy raises ValueError."""
        from app.schemas.strategy import StrategyCreate
        
        repo = StrategyRepository(db)
        repo.create(StrategyCreate(**sample_strategy_data))
        
        with pytest.raises(ValueError, match="already exists"):
            repo.create(StrategyCreate(**sample_strategy_data))

    def test_get_strategy(self, db: Session, sample_strategy_data: dict):
        """Test retrieving a strategy by ID."""
        from app.schemas.strategy import StrategyCreate
        
        repo = StrategyRepository(db)
        created = repo.create(StrategyCreate(**sample_strategy_data))
        
        retrieved = repo.get(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_nonexistent_returns_none(self, db: Session):
        """Test that getting non-existent strategy returns None."""
        repo = StrategyRepository(db)
        result = repo.get(99999)
        
        assert result is None

    def test_list_and_count(self, db: Session, sample_strategy_data: dict):
        """Test listing strategies with count."""
        from app.schemas.strategy import StrategyCreate, StrategyQuery
        
        repo = StrategyRepository(db)
        
        # Create multiple strategies
        for i in range(3):
            repo.create(
                StrategyCreate(**{**sample_strategy_data, "name": f"Strategy {i}"})
            )
        
        # List all
        query = StrategyQuery()
        rows, total = repo.list_and_count(query)
        
        assert total == 3
        assert len(rows) == 3

    def test_update_strategy(self, db: Session, sample_strategy_data: dict):
        """Test updating a strategy."""
        from app.schemas.strategy import StrategyCreate, StrategyUpdate
        
        repo = StrategyRepository(db)
        strategy = repo.create(StrategyCreate(**sample_strategy_data))
        
        # Update
        update = StrategyUpdate(name="Updated Name", is_active=False)
        updated = repo.update(strategy, update)
        
        assert updated.name == "Updated Name"
        assert updated.is_active is False

    def test_delete_strategy(self, db: Session, sample_strategy_data: dict):
        """Test deleting a strategy."""
        from app.schemas.strategy import StrategyCreate
        
        repo = StrategyRepository(db)
        strategy = repo.create(StrategyCreate(**sample_strategy_data))
        strategy_id = strategy.id
        
        # Delete
        repo.delete(strategy)
        
        # Verify deletion
        assert repo.get(strategy_id) is None