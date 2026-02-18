from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

async def calculate_monthly_revenue(property_id: str, tenant_id: str, month: int, year: int, db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month in the property's local timezone.
    """
    validate_month_year(month, year)

    owns_session = db_session is None
    session = db_session

    try:
        if session is None:
            from app.core.database_pool import DatabasePool
            db_pool = DatabasePool()
            await db_pool.initialize()
            if not db_pool.session_factory:
                raise Exception("Database pool not available")
            session = await db_pool.get_session()

        from sqlalchemy import text
        query = text(
            """
            SELECT COALESCE(SUM(r.total_amount), 0) AS total_revenue
            FROM reservations r
            JOIN properties p
              ON p.id = r.property_id
             AND p.tenant_id = r.tenant_id
            WHERE r.property_id = :property_id
              AND r.tenant_id = :tenant_id
              AND EXTRACT(YEAR FROM (r.check_in_date AT TIME ZONE p.timezone)) = :year
              AND EXTRACT(MONTH FROM (r.check_in_date AT TIME ZONE p.timezone)) = :month
            """
        )
        result = await session.execute(
            query,
            {
                "property_id": property_id,
                "tenant_id": tenant_id,
                "year": year,
                "month": month,
            },
        )
        row = result.fetchone()
        return Decimal(str(row.total_revenue if row else 0))
    finally:
        if owns_session and session is not None:
            await session.close()

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
        # Import database pool
        from app.core.database_pool import DatabasePool
        
        # Initialize pool if needed
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            session = await db_pool.get_session()
            async with session:
                # Use SQLAlchemy text for raw SQL
                from sqlalchemy import text
                
                date_filter = ""
                if month is not None and year is not None:
                    # Filter by property's local timezone calendar month.
                    date_filter = """
                        AND EXTRACT(YEAR FROM (r.check_in_date AT TIME ZONE p.timezone)) = :year
                        AND EXTRACT(MONTH FROM (r.check_in_date AT TIME ZONE p.timezone)) = :month
                    """
                query = text(f"""
                    SELECT 
                        r.property_id,
                        COALESCE(SUM(r.total_amount), 0) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations r
                    JOIN properties p
                      ON p.id = r.property_id
                     AND p.tenant_id = r.tenant_id
                    WHERE r.property_id = :property_id
                      AND r.tenant_id = :tenant_id
                      {date_filter}
                    GROUP BY r.property_id
                """)
                
                params = {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                }
                if month is not None and year is not None:
                    params["month"] = month
                    params["year"] = year

                result = await session.execute(query, params)
                row = result.fetchone()
                
                if row:
                    total_revenue = Decimal(str(row.total_revenue))
                    # Financial policy: round the aggregated total once for display/export.
                    total_revenue_rounded = total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue_rounded),
                        "currency": "USD", 
                        "count": row.reservation_count
                    }
                else:
                    # No reservations found for this property
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": "0.00",
                        "currency": "USD",
                        "count": 0
                    }
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        # Create property-specific mock data for testing when DB is unavailable
        # This ensures each property shows different figures
        mock_data = {
            'prop-001': {'total': '1000.00', 'count': 3},
            'prop-002': {'total': '4975.50', 'count': 4}, 
            'prop-003': {'total': '6100.50', 'count': 2},
            'prop-004': {'total': '1776.50', 'count': 4},
            'prop-005': {'total': '3256.00', 'count': 3}
        }
        
        mock_property_data = mock_data.get(property_id, {'total': '0.00', 'count': 0})
        
        return {
            "property_id": property_id,
            "tenant_id": tenant_id, 
            "total": mock_property_data['total'],
            "currency": "USD",
            "count": mock_property_data['count']
        }
