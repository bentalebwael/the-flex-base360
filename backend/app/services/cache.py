import json
import redis.asyncio as redis
from typing import Dict, Any, Optional
import os
import logging

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
logger = logging.getLogger(__name__)


def get_revenue_cache_key(property_id: str, tenant_id: str) -> str:
    """Scope revenue cache entries to both tenant and property."""
    return f"revenue:{tenant_id}:{property_id}"


async def get_revenue_summary(property_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    cache_key = get_revenue_cache_key(property_id, tenant_id)
    
    try:
        cached = await redis_client.get(cache_key)
    except Exception as exc:
        logger.warning("Revenue cache read failed for %s: %s", cache_key, exc)
        cached = None

    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    if result is None:
        return None
    
    # Cache the result for 5 minutes
    try:
        await redis_client.setex(cache_key, 300, json.dumps(result))
    except Exception as exc:
        logger.warning("Revenue cache write failed for %s: %s", cache_key, exc)
    
    return result
