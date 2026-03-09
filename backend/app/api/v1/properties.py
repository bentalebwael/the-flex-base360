from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import authenticate_request as get_current_user
from app.config import settings
import asyncpg
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/properties")
async def list_properties(current_user=Depends(get_current_user)):
    tenant_id = current_user.tenant_id

    try:
        conn = await asyncpg.connect(settings.database_url)
        try:
            rows = await conn.fetch(
                "SELECT id, name FROM properties WHERE tenant_id = $1",
                tenant_id
            )
        finally:
            await conn.close()

        return {"data": [{"id": r["id"], "name": r["name"]} for r in rows], "total": len(rows)}

    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=str(e))