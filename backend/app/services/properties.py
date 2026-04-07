from typing import List, Dict, Any
from sqlalchemy import text
from app.core.database_pool import DatabasePool


async def get_properties_by_tenant(tenant_id: str) -> List[Dict[str, Any]]:
    """
    Fetches properties for a given tenant from the database.
    """
    db_pool = DatabasePool()
    await db_pool.initialize()

    async with db_pool.get_session() as session:
        result = await session.execute(
            text("SELECT id, name FROM properties WHERE tenant_id = :tenant_id ORDER BY id"),
            {"tenant_id": tenant_id}
        )
        rows = result.fetchall()

    return [{"id": row.id, "name": row.name} for row in rows]
