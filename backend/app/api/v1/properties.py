import logging
import asyncpg
from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.core.auth import authenticate_request as get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/properties", response_model=List[Dict[str, Any]])
async def get_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Return properties belonging to the authenticated tenant."""
    tenant_id = getattr(current_user, "tenant_id", None)
    logger.info(f"Fetching properties for tenant: {tenant_id}")

    # settings.database_url is "postgresql://..." — asyncpg uses this format directly
    conn = await asyncpg.connect(settings.database_url)
    try:
        rows = await conn.fetch(
            "SELECT id, name, timezone FROM properties WHERE tenant_id = $1 ORDER BY name",
            tenant_id
        )
        return [{"id": r["id"], "name": r["name"], "timezone": r["timezone"]} for r in rows]
    finally:
        await conn.close()
