import json
import redis.asyncio as redis
from typing import Dict, Any
import os

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

async def get_revenue_summary(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    # Bug #1 FIX: Cache key must include tenant_id to prevent cross-tenant data leaks.
    # Without tenant_id, two tenants sharing the same property_id (e.g. prop-001) would
    # read each other's cached revenue — a critical privacy violation.
    # Bug #1 OLD (vulnerable): cache_key = f"revenue:{property_id}"
    cache_key = f"revenue:{tenant_id}:{property_id}"  # Bug #1 FIXED
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id)
    
    # Cache the result for 5 minutes
    await redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
