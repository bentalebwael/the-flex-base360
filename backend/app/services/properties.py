from typing import Any, Dict, List

from sqlalchemy import text

from app.core.database_pool import db_pool


async def list_tenant_properties(tenant_id: str) -> List[Dict[str, Any]]:
    """Return the properties visible to the authenticated tenant."""
    await db_pool.initialize()

    async with db_pool.get_session() as session:
        query = text(
            """
            SELECT id, name, timezone
            FROM properties
            WHERE tenant_id = :tenant_id
            ORDER BY name ASC
            """
        )
        result = await session.execute(query, {"tenant_id": tenant_id})

        return [
            {
                "id": row.id,
                "name": row.name,
                "timezone": row.timezone,
            }
            for row in result.fetchall()
        ]
