
import json
from typing import Dict, Any
import os
import logging

# Add an In-memory cache fallback
class InMemoryCache:
    def __init__(self):
        self.store = {}
    async def get(self, key):
        return self.store.get(key)
    async def setex(self, key, ttl, value):
        self.store[key] = value

try:
    import redis.asyncio as redis
    redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    # Test connection
    async def test_redis():
        try:
            await redis_client.ping()
            return redis_client
        except Exception as e:
            logging.warning(f"Redis connection failed: {e}. Using in-memory cache.")
            return InMemoryCache()
    import asyncio
    redis_client = asyncio.run(test_redis())
except Exception as e:
    logging.warning(f"Redis import or connection failed: {e}. Using in-memory cache.")
    redis_client = InMemoryCache()

async def get_revenue_summary(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    cache_key = f"revenue:{tenant_id}:{property_id}"
    # Try to get from cache
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            # If Redis, decode bytes; if in-memory, use as is
            if isinstance(cached, bytes):
                cached = cached.decode()
            return json.loads(cached)
    except Exception as e:
        logging.warning(f"Cache get failed: {e}")
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    # Cache the result for 5 minutes
    try:
        await redis_client.setex(cache_key, 300, json.dumps(result))
    except Exception as e:
        logging.warning(f"Cache set failed: {e}")
    return result
