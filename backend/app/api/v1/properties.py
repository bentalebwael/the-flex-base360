from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import asyncpg
import os
import logging

from app.core.auth import authenticate_request

router = APIRouter()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/propertyflow")


async def get_db_connection():
    """Open a single asyncpg connection using the container DATABASE_URL."""
    # asyncpg expects the scheme to be 'postgresql', not 'postgres'
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    return await asyncpg.connect(url)


@router.get("/properties")
async def list_properties(
    current_user=Depends(authenticate_request),
) -> Dict[str, Any]:
    """
    Returns all properties belonging to the authenticated user's tenant.

    This endpoint is what makes the dashboard tenant-aware. Previously the
    frontend used a hardcoded PROPERTIES constant listing all five properties
    across both tenants, so every user saw the same list regardless of who
    they were. Now the frontend calls this endpoint, which scopes the query
    to the current user's tenant_id from their auth token.
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant associated with this account.")

    conn = None
    try:
        conn = await get_db_connection()
        rows = await conn.fetch(
            """
            SELECT id, name, timezone
            FROM properties
            WHERE tenant_id = $1
            ORDER BY name
            """,
            tenant_id,
        )
        items = [dict(row) for row in rows]
        logger.info(f"Returning {len(items)} properties for tenant {tenant_id}")
        return {"items": items, "total": len(items)}

    except Exception as e:
        logger.error(f"Failed to fetch properties for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to load properties.")
    finally:
        if conn:
            await conn.close()