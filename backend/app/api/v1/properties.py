from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/properties")
async def list_properties(
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return properties that belong to the authenticated tenant."""
    from app.core.database_pool import DatabasePool
    from sqlalchemy import text

    tenant_id = getattr(current_user, "tenant_id", None) or "default_tenant"

    db_pool = DatabasePool()
    await db_pool.initialize()

    if db_pool.session_factory:
        async with db_pool.get_session() as session:
            result = await session.execute(
                text("SELECT id, name FROM properties WHERE tenant_id = :tid ORDER BY name"),
                {"tid": tenant_id},
            )
            rows = result.fetchall()
            items = [{"id": r.id, "name": r.name} for r in rows]
    else:
        items = []

    return {"items": items, "total": len(items)}
