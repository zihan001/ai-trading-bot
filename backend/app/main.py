from fastapi import FastAPI
import os
import asyncpg
import redis.asyncio as aioredis

from app.api.routes.strategies import router as strategies_router
from app.api.routes.assets import router as assets_router
from app.api.routes.symbols import router as symbols_router
from app.api.routes.orders import router as orders_router

app = FastAPI(title="AI Trading Bot", version="0.1.0")

@app.get("/health")
async def health():
    # check env presence
    env_ok = all([
        os.getenv("POSTGRES_HOST"),
        os.getenv("REDIS_URL"),
        os.getenv("JWT_SECRET"),
    ])

    # check postgres
    pg_ok = False
    try:
        async with await asyncpg.connect(
            user=os.getenv("POSTGRES_USER", "bot"),
            password=os.getenv("POSTGRES_PASSWORD", "bot"),
            database=os.getenv("POSTGRES_DB", "trading"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
        ) as conn:
            await conn.execute("SELECT 1;")
        pg_ok = True
    except Exception:
        pg_ok = False

    # check redis
    redis_ok = False
    r = None
    try:
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        pong = await r.ping()
        redis_ok = bool(pong)
    except Exception:
        redis_ok = False
    finally:
        if r is not None:
            await r.aclose()

    status = "ok" if (env_ok and pg_ok and redis_ok) else "degraded"
    return {"status": status, "env": env_ok, "postgres": pg_ok, "redis": redis_ok}

@app.get("/broker/status")
def broker_status():
    broker = os.getenv("BROKER", "alpaca")
    base = os.getenv("ALPACA_BASE_URL")
    has_key = bool(os.getenv("ALPACA_API_KEY_ID"))
    has_secret = bool(os.getenv("ALPACA_API_SECRET_KEY"))
    # Not calling the broker yet; just reporting readiness.
    return {
        "broker": broker,
        "base_url": base,
        "api_key_present": has_key,
        "api_secret_present": has_secret
    }

# Include routers
app.include_router(strategies_router)
app.include_router(assets_router)
app.include_router(symbols_router)
app.include_router(orders_router)