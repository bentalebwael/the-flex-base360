from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, List

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

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    import asyncpg
    from app.config import settings

    start_of_month = datetime(2024, 3, 1, tzinfo=timezone.utc)
    end_of_month = datetime(2024, 4, 1, tzinfo=timezone.utc)

    conn = await asyncpg.connect(settings.database_url)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                SUM(total_amount) AS total_revenue,
                COUNT(*) AS reservation_count
            FROM reservations
            WHERE property_id = $1 AND tenant_id = $2
              AND check_in_date >= $3
              AND check_in_date < $4
            """,
            property_id,
            tenant_id,
            start_of_month,
            end_of_month,
        )
        total_revenue = Decimal(str(row["total_revenue"])) if row["total_revenue"] else Decimal("0")
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": str(total_revenue),
            "currency": "USD",
            "count": row["reservation_count"],
        }
    finally:
        await conn.close()
