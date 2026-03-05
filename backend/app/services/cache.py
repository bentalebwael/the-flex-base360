import json
import redis.asyncio as redis
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

async def get_revenue_summary(
    property_id: str,
    tenant_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    use_cache = month is not None and year is not None
    cache_key = ""
    if use_cache:
        period_key = f"{year}-{month}"
        # Tenant-aware cache key to prevent cross-tenant data leakage.
        cache_key = f"revenue:{tenant_id}:{property_id}:{period_key}"
        
        # Try to get from cache for explicit month/year queries only.
        try:
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as cache_read_error:
            logger.warning(
                "Revenue cache read failed for key %s: %s",
                cache_key,
                cache_read_error,
            )
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(
        property_id,
        tenant_id,
        month=month,
        year=year,
    )
    
    # Cache explicit month/year queries for 5 minutes.
    if use_cache:
        try:
            await redis_client.setex(cache_key, 300, json.dumps(result))
        except Exception as cache_write_error:
            logger.warning(
                "Revenue cache write failed for key %s: %s",
                cache_key,
                cache_write_error,
            )
    
    return result
