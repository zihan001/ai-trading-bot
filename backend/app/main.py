from fastapi import FastAPI
import os
import asyncpg
import redis.asyncio as aioredis

app = FastAPI(title="AI Trading Bot – Minimal")

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
        conn = await asyncpg.connect(
            user=os.getenv("POSTGRES_USER", "bot"),
            password=os.getenv("POSTGRES_PASSWORD", "bot"),
            database=os.getenv("POSTGRES_DB", "trading"),
            host=os.getenv("POSTGRES_HOST", "postgres"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
        )
        await conn.execute("SELECT 1;")
        await conn.close()
        pg_ok = True
    except Exception:
        pg_ok = False

    # check redis
    redis_ok = False
    try:
        r = aioredis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
        pong = await r.ping()
        redis_ok = bool(pong)
        await r.aclose()
    except Exception:
        redis_ok = False

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
