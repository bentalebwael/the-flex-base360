from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

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

async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        from app.core.database_pool import db_pool
        from sqlalchemy import text

        if not db_pool.session_factory:
            await db_pool.initialize()

        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        async with (await db_pool.get_session()) as session:
            sql = """
                SELECT
                    r.property_id,
                    SUM(r.total_amount) as total_revenue,
                    COUNT(*) as reservation_count,
                    COALESCE(MAX(r.currency), 'USD') as currency
                FROM reservations r
                JOIN properties p ON p.id = r.property_id AND p.tenant_id = r.tenant_id
                WHERE r.property_id = :property_id
                  AND r.tenant_id = :tenant_id
            """

            params = {
                "property_id": property_id,
                "tenant_id": tenant_id,
            }

            if month is not None and year is not None:
                sql += """
                  AND (r.check_in_date AT TIME ZONE p.timezone) >= make_timestamp(CAST(:year AS INTEGER), CAST(:month AS INTEGER), 1, 0, 0, 0)
                  AND (r.check_in_date AT TIME ZONE p.timezone) < (make_timestamp(CAST(:year AS INTEGER), CAST(:month AS INTEGER), 1, 0, 0, 0) + INTERVAL '1 month')
                """
                params["month"] = month
                params["year"] = year

            sql += """
                GROUP BY r.property_id
            """

            result = await session.execute(text(sql), params)
            row = result.fetchone()

            if not row:
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": "0.00",
                    "currency": "USD",
                    "count": 0
                }

            total_revenue = Decimal(str(row.total_revenue)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            return {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "total": str(total_revenue),
                "currency": row.currency,
                "count": row.reservation_count
            }

    except Exception as e:
        logger.error("Database error for %s (tenant: %s): %s", property_id, tenant_id, e)
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": "0.00",
            "currency": "USD",
            "count": 0
        }
