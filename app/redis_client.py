import os
import json
import redis.asyncio as aioredis

REDIS_URL   = os.getenv("REDIS_URL", "redis://localhost:6379")
WINDOW_SIZE = 100   # keep last 100 readings per sensor+metric combo
TTL_SECONDS = 7200  # auto-expire keys after 2 hours of inactivity

_redis: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def _key(sensor_id: str, metric_name: str) -> str:
    return f"sensor:{sensor_id}:{metric_name}"


async def push_value(sensor_id: str, metric_name: str, value: float) -> None:
    """Append value to the sliding window list, trimming to WINDOW_SIZE."""
    r   = await get_redis()
    key = _key(sensor_id, metric_name)
    await r.rpush(key, json.dumps(value))
    await r.ltrim(key, -WINDOW_SIZE, -1)
    await r.expire(key, TTL_SECONDS)


async def get_window(sensor_id: str, metric_name: str) -> list[float]:
    """Return the current sliding window as a list of floats."""
    r      = await get_redis()
    key    = _key(sensor_id, metric_name)
    items  = await r.lrange(key, 0, -1)
    return [json.loads(v) for v in items]


async def get_all_sensor_keys() -> list[str]:
    """Return all active sensor:metric keys in Redis."""
    r    = await get_redis()
    keys = await r.keys("sensor:*")
    # Strip the "sensor:" prefix so callers get "sensor_id:metric_name"
    return [k.replace("sensor:", "", 1) for k in keys]


async def close_redis():
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
