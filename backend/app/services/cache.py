import json
import redis.asyncio as redis
from typing import Dict, Any
import os

# Initialize Redis client (typically configured centrally).
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

def financial_json_serializer(obj):
    """
    Serializes objects not supported by default json module.
    Crucial: Converts Decimal to string to prevent floating-point precision loss.
    """
    if isinstance(obj, Decimal):
        return str(obj) # "1250.50" (Safe) instead of 1250.5 (Unsafe float)
    raise TypeError(f"Type {type(obj)} not serializable")

async def get_revenue_summary(
    property_id: str, 
    tenant_id: str,
    month: int = None,
    year: int = None
) -> Dict[str, Any]:
    """
    Fetches revenue summary, utilizing caching to improve performance.
    """
    cache_key = f"tenant:{tenant_id}:revenue:prop:{property_id}:m:{month}:y:{year}"
    
    # Try to get from cache
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Revenue calculation is delegated to the reservation service.
    from app.services.reservations import calculate_total_revenue
    
    # Calculate revenue
    result = await calculate_total_revenue(property_id, tenant_id, month, year)
    
    # Use our strict financial serializer
    json_result = json.dumps(result, default=financial_json_serializer)
    # Cache the result for 60 seconds
    await redis_client.setex(cache_key, 60, json_result)
    
    return result
