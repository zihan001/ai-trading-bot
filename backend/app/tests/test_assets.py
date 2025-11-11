import uuid
from httpx import AsyncClient

def sample():
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "asset_type": "equity",
        "currency": "USD",
        "is_active": True
    }

async def test_create_and_get(async_client: AsyncClient):
    r = await async_client.post("/assets", json=sample())
    assert r.status_code == 201, r.text
    data = r.json()
    asset_id = data["id"]

    r2 = await async_client.get(f"/assets/{asset_id}")
    assert r2.status_code == 200
    assert r2.json()["symbol"] == "AAPL"

async def test_unique_exchange_symbol(async_client: AsyncClient):
    await async_client.post("/assets", json=sample())
    r = await async_client.post("/assets", json=sample())
    assert r.status_code == 409

async def test_list_filters(async_client: AsyncClient):
    await async_client.post("/assets", json=sample())
    r = await async_client.get("/assets?exchange=NASDAQ&symbol=AAPL")
    assert r.status_code == 200
    payload = r.json()
    assert payload["total"] >= 1
    assert any(item["symbol"] == "AAPL" for item in payload["items"])
