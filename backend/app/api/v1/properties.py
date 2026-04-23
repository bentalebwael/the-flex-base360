from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List

from app.core.auth import authenticate_request as get_current_user

router = APIRouter()


@router.get("/properties")
async def list_properties(current_user=Depends(get_current_user)) -> List[Dict[str, Any]]:
    """
    Return the authenticated tenant's properties.

    The tenant_id is taken from the validated JWT on `current_user`. There is no
    query parameter override, by design — this is the preventive pattern that stops
    a future caller from asking for another tenant's property list.
    """
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        # Fail-closed: missing tenant context is an authentication problem, not a
        # data-layer fallback. Do NOT invent a default or return an empty list here.
        raise HTTPException(status_code=401, detail="Authenticated user missing tenant_id")

    from app.core.database_pool import DatabasePool

    db_pool = DatabasePool()
    await db_pool.initialize()
    if not db_pool.session_factory:
        raise HTTPException(status_code=503, detail="Database unavailable")

    from sqlalchemy import text

    async with db_pool.get_session() as session:
        result = await session.execute(
            text(
                "SELECT id, name, timezone "
                "FROM properties "
                "WHERE tenant_id = :tenant_id "
                "ORDER BY id"
            ),
            {"tenant_id": tenant_id},
        )
        rows = result.fetchall()
        return [
            {"id": row.id, "name": row.name, "timezone": row.timezone}
            for row in rows
        ]
