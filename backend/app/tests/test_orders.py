import pytest
import uuid
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, OrderType, TimeInForce
from app.repositories.order_repo import OrderRepository
from app.schemas.order import OrderCreate, OrderUpdate, OrderQuery


@pytest.mark.asyncio
class TestOrderEndpoints:
    """Test order CRUD endpoints."""

    async def test_create_order_limit_success(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test creating a limit order."""
        response = await async_client.post("/orders", json=sample_order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["side"] == "buy"
        assert data["type"] == "limit"
        assert Decimal(data["quantity"]) == Decimal("100")
        assert Decimal(data["price"]) == Decimal("150.50")
        assert data["status"] == "new"
        assert "id" in data
        assert "created_at" in data

    async def test_create_order_market(
        self, async_client: AsyncClient
    ):
        """Test creating a market order (no price required)."""
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "side": "sell",
            "type": "market",
            "quantity": "50",
            "time_in_force": "day",
            "paper": True
        }
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "market"
        assert data["price"] is None

    async def test_create_order_stop_limit(
        self, async_client: AsyncClient
    ):
        """Test creating a stop-limit order (both price and stop_price required)."""
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "side": "buy",
            "type": "stop_limit",
            "quantity": "100",
            "price": "150.00",
            "stop_price": "148.00",
            "time_in_force": "gtc",
            "paper": True
        }
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "stop_limit"
        assert Decimal(data["price"]) == Decimal("150.00")
        assert Decimal(data["stop_price"]) == Decimal("148.00")

    async def test_create_order_missing_price_for_limit(
        self, async_client: AsyncClient
    ):
        """Test that limit orders without price are rejected."""
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "side": "buy",
            "type": "limit",
            "quantity": "100",
            # Missing price
            "paper": True
        }
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 422
        assert "price is required" in response.text.lower()

    async def test_create_order_missing_stop_price_for_stop(
        self, async_client: AsyncClient
    ):
        """Test that stop orders without stop_price are rejected."""
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "side": "sell",
            "type": "stop",
            "quantity": "50",
            # Missing stop_price
            "paper": True
        }
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 422
        assert "stop_price is required" in response.text.lower()

    async def test_create_order_invalid_time_in_force(
        self, async_client: AsyncClient
    ):
        """Test that FOK/IOC are rejected for stop orders."""
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "side": "buy",
            "type": "stop",
            "quantity": "100",
            "stop_price": "150.00",
            "time_in_force": "fok",  # Invalid for stop orders
            "paper": True
        }
        response = await async_client.post("/orders", json=order_data)
        
        assert response.status_code == 422

    async def test_create_order_duplicate_client_order_id(
        self, async_client: AsyncClient
    ):
        """Test idempotency - duplicate client_order_id is rejected."""
        account_id = str(uuid.uuid4())
        order_data = {
            "symbol_id": str(uuid.uuid4()),
            "account_id": account_id,
            "side": "buy",
            "type": "market",
            "quantity": "100",
            "client_order_id": "unique-123",
            "paper": True
        }
        
        # Create first order
        response1 = await async_client.post("/orders", json=order_data)
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await async_client.post("/orders", json=order_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    async def test_get_order_success(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test retrieving an order by ID."""
        # Create order
        create_response = await async_client.post("/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Get order
        response = await async_client.get(f"/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert data["side"] == sample_order_data["side"]

    async def test_get_order_not_found(self, async_client: AsyncClient):
        """Test retrieving a non-existent order."""
        fake_id = str(uuid.uuid4())
        response = await async_client.get(f"/orders/{fake_id}")
        
        assert response.status_code == 404

    async def test_list_orders_empty(self, async_client: AsyncClient):
        """Test listing orders when none exist."""
        response = await async_client.get("/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    async def test_list_orders_with_data(
        self, async_client: AsyncClient
    ):
        """Test listing orders with data."""
        symbol_id = str(uuid.uuid4())
        
        # Create multiple orders
        for i in range(3):
            order_data = {
                "symbol_id": symbol_id,
                "side": "buy",
                "type": "market",
                "quantity": str(10 * (i + 1)),
                "paper": True
            }
            await async_client.post("/orders", json=order_data)
        
        # List all
        response = await async_client.get("/orders")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    async def test_list_orders_filter_by_symbol(
        self, async_client: AsyncClient
    ):
        """Test filtering orders by symbol_id."""
        symbol_id = str(uuid.uuid4())
        other_symbol_id = str(uuid.uuid4())
        
        # Create orders for different symbols
        await async_client.post("/orders", json={
            "symbol_id": symbol_id,
            "side": "buy",
            "type": "market",
            "quantity": "100",
            "paper": True
        })
        await async_client.post("/orders", json={
            "symbol_id": other_symbol_id,
            "side": "sell",
            "type": "market",
            "quantity": "50",
            "paper": True
        })
        
        # Filter by symbol_id
        response = await async_client.get(f"/orders?symbol_id={symbol_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["symbol_id"] == symbol_id

    async def test_list_orders_filter_by_status(
        self, async_client: AsyncClient
    ):
        """Test filtering orders by status."""
        # Create orders
        response1 = await async_client.post("/orders", json={
            "symbol_id": str(uuid.uuid4()),
            "side": "buy",
            "type": "market",
            "quantity": "100",
            "paper": True
        })
        order_id = response1.json()["id"]
        
        await async_client.post("/orders", json={
            "symbol_id": str(uuid.uuid4()),
            "side": "sell",
            "type": "market",
            "quantity": "50",
            "paper": True
        })
        
        # Cancel one order
        await async_client.delete(f"/orders/{order_id}")
        
        # Filter by status=new
        response = await async_client.get("/orders?status=new")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "new"

    async def test_update_order_success(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test updating order price."""
        # Create order
        create_response = await async_client.post("/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Update order
        update_data = {
            "price": "155.00",
            "notes": "Updated price"
        }
        response = await async_client.patch(f"/orders/{order_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["price"]) == Decimal("155.00")
        assert data["notes"] == "Updated price"

    async def test_update_order_wrong_status(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test that orders in terminal states cannot be updated."""
        # Create and cancel order
        create_response = await async_client.post("/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        await async_client.delete(f"/orders/{order_id}")
        
        # Try to update canceled order
        response = await async_client.patch(
            f"/orders/{order_id}",
            json={"price": "160.00"}
        )
        
        assert response.status_code == 409
        assert "cannot update" in response.json()["detail"].lower()

    async def test_cancel_order_success(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test canceling an order."""
        # Create order
        create_response = await async_client.post("/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Cancel order
        response = await async_client.delete(f"/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "canceled"
        assert data["canceled_at"] is not None

    async def test_cancel_order_idempotent(
        self, async_client: AsyncClient, sample_order_data: dict
    ):
        """Test that canceling an already canceled order is idempotent."""
        # Create order
        create_response = await async_client.post("/orders", json=sample_order_data)
        order_id = create_response.json()["id"]
        
        # Cancel twice
        response1 = await async_client.delete(f"/orders/{order_id}")
        assert response1.status_code == 200
        
        response2 = await async_client.delete(f"/orders/{order_id}")
        assert response2.status_code == 409  # Cannot cancel already canceled order


class TestOrderRepository:
    """Test order repository methods directly."""

    def test_create_order(self, db: Session):
        """Test creating an order via repository."""
        from app.schemas.order import OrderCreate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="buy",
            type=OrderType.limit,
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            time_in_force=TimeInForce.day,
            paper=True
        )
        
        repo = OrderRepository(db)
        order = repo.create(order_data)
        
        assert order.id is not None
        assert order.status == OrderStatus.new
        assert order.quantity == Decimal("100")

    def test_create_order_duplicate_client_order_id(self, db: Session):
        """Test that duplicate client_order_id raises ValueError."""
        from app.schemas.order import OrderCreate
        
        account_id = uuid.uuid4()
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            account_id=account_id,
            side="buy",
            type=OrderType.market,
            quantity=Decimal("100"),
            client_order_id="unique-123",
            paper=True
        )
        
        repo = OrderRepository(db)
        repo.create(order_data)
        
        with pytest.raises(ValueError, match="already exists"):
            repo.create(order_data)

    def test_get_order(self, db: Session):
        """Test retrieving an order by ID."""
        from app.schemas.order import OrderCreate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="sell",
            type=OrderType.market,
            quantity=Decimal("50"),
            paper=True
        )
        
        repo = OrderRepository(db)
        created = repo.create(order_data)
        
        retrieved = repo.get(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.side == created.side

    def test_list_and_count(self, db: Session):
        """Test listing orders with count."""
        from app.schemas.order import OrderCreate, OrderQuery
        
        repo = OrderRepository(db)
        symbol_id = uuid.uuid4()
        
        # Create multiple orders
        for i in range(3):
            order_data = OrderCreate(
                symbol_id=symbol_id,
                side="buy",
                type=OrderType.market,
                quantity=Decimal(str(10 * (i + 1))),
                paper=True
            )
            repo.create(order_data)
        
        # List all
        query = OrderQuery()
        rows, total = repo.list_and_count(query)
        
        assert total == 3
        assert len(rows) == 3

    def test_update_order(self, db: Session):
        """Test updating an order."""
        from app.schemas.order import OrderCreate, OrderUpdate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="buy",
            type=OrderType.limit,
            quantity=Decimal("100"),
            price=Decimal("150.00"),
            paper=True
        )
        
        repo = OrderRepository(db)
        order = repo.create(order_data)
        
        # Update
        update = OrderUpdate(price=Decimal("155.00"), notes="Updated")
        updated = repo.update(order, update)
        
        assert updated.price == Decimal("155.00")
        assert updated.notes == "Updated"

    def test_update_order_wrong_status(self, db: Session):
        """Test that orders in terminal states cannot be updated."""
        from app.schemas.order import OrderCreate, OrderUpdate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="buy",
            type=OrderType.market,
            quantity=Decimal("100"),
            paper=True
        )
        
        repo = OrderRepository(db)
        order = repo.create(order_data)
        
        # Cancel order
        order = repo.cancel(order)
        
        # Try to update
        update = OrderUpdate(notes="Should fail")
        with pytest.raises(ValueError, match="Cannot update"):
            repo.update(order, update)

    def test_cancel_order(self, db: Session):
        """Test canceling an order."""
        from app.schemas.order import OrderCreate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="buy",
            type=OrderType.market,
            quantity=Decimal("100"),
            paper=True
        )
        
        repo = OrderRepository(db)
        order = repo.create(order_data)
        
        # Cancel
        canceled = repo.cancel(order)
        
        assert canceled.status == OrderStatus.canceled
        assert canceled.canceled_at is not None

    def test_cancel_order_wrong_status(self, db: Session):
        """Test that filled orders cannot be canceled."""
        from app.schemas.order import OrderCreate
        
        order_data = OrderCreate(
            symbol_id=uuid.uuid4(),
            side="buy",
            type=OrderType.market,
            quantity=Decimal("100"),
            paper=True
        )
        
        repo = OrderRepository(db)
        order = repo.create(order_data)
        
        # Manually set to filled
        order.status = OrderStatus.filled
        db.commit()
        db.refresh(order)
        
        # Try to cancel
        with pytest.raises(ValueError, match="Cannot cancel"):
            repo.cancel(order)