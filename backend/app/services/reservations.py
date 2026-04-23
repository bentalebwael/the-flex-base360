from datetime import datetime
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

async def calculate_total_revenue(
    property_id: str,
    tenant_id: str,
    month: int = None,
    year: int = None,
) -> Dict[str, Any]:
    """
    Aggregates revenue from database, optionally filtered to a single month.

    When `month` and `year` are both provided, the sum is restricted to reservations
    whose `check_in_date` falls in `[year-month-01, next-month-01)` at UTC boundaries.
    Timezone-aware boundaries come in the Bug 4 follow-up.
    """
    try:
        # Import database pool
        from app.core.database_pool import DatabasePool

        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()

        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text

                params = {"property_id": property_id, "tenant_id": tenant_id}
                month_filter_sql = ""
                if month is not None and year is not None:
                    start_date = datetime(year, month, 1)
                    end_date = (
                        datetime(year, month + 1, 1)
                        if month < 12
                        else datetime(year + 1, 1, 1)
                    )
                    params["start_date"] = start_date
                    params["end_date"] = end_date
                    month_filter_sql = (
                        " AND check_in_date >= :start_date"
                        " AND check_in_date < :end_date"
                    )

                query = text(f"""
                    SELECT
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    {month_filter_sql}
                    GROUP BY property_id
                """)

                result = await session.execute(query, params)
                row = result.fetchone()

                if row:
                    total_revenue = Decimal(str(row.total_revenue))
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
                        "currency": "USD",
                        "count": row.reservation_count,
                    }
                else:
                    # No reservations in the requested scope
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.000",
                        "currency": "USD",
                        "count": 0,
                    }
        else:
            raise Exception("Database pool not available")

    except Exception as e:
        # Surface DB failures to the caller. The previous mock_data fallback
        # fabricated per-property numbers without tenant scoping, which both
        # masked real outages and broke tenant isolation.
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        raise
