from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from sqlalchemy import text

from app.core.database_pool import db_pool

async def calculate_monthly_revenue(property_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month.
    """

    start_date = datetime(year, month, 1)
    if month < 12:
        end_date = datetime(year, month + 1, 1)
    else:
        end_date = datetime(year + 1, 1, 1)
        
    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date}")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized


async def calculate_total_revenue(property_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
    """
    Aggregate revenue for a tenant-scoped property.
    """
    await db_pool.initialize()

    async with db_pool.get_session() as session:
        query = text(
            """
            SELECT
                p.id AS property_id,
                COALESCE(SUM(r.total_amount), 0) AS total_revenue,
                COUNT(r.id) AS reservation_count,
                COALESCE(MAX(r.currency), 'USD') AS currency
            FROM properties p
            LEFT JOIN reservations r
                ON r.property_id = p.id
               AND r.tenant_id = p.tenant_id
            WHERE p.id = :property_id
              AND p.tenant_id = :tenant_id
            GROUP BY p.id
            """
        )

        result = await session.execute(
            query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
            },
        )
        row = result.fetchone()

        if row is None:
            return None

        return {
            "property_id": row.property_id,
            "tenant_id": tenant_id,
            "total": str(Decimal(str(row.total_revenue))),
            "currency": row.currency,
            "count": int(row.reservation_count),
        }
