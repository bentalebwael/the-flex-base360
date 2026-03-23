from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List

async def calculate_monthly_revenue(property_id: str, month: int, year: int, timezone: str = 'UTC', db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month using the property's local timezone.
    """
    from zoneinfo import ZoneInfo

    # FIX: Was using naive UTC datetimes for month boundaries, ignoring the property's timezone.
    # E.g. res-tz-1 with check_in '2024-02-29 23:30:00 UTC' is February in UTC,
    # but March in Europe/Paris (00:30 on the 1st). Without this conversion, the $1250
    # reservation was classified in the wrong month.
    tz = ZoneInfo(timezone)
    start_date = datetime(year, month, 1, tzinfo=tz)
    if month < 12:
        end_date = datetime(year, month + 1, 1, tzinfo=tz)
    else:
        end_date = datetime(year + 1, 1, 1, tzinfo=tz)
        
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
                
                query = text("""
                    SELECT 
                        property_id,
                        SUM(total_amount) as total_revenue,
                        COUNT(*) as reservation_count
                    FROM reservations 
                    WHERE property_id = :property_id AND tenant_id = :tenant_id
                    GROUP BY property_id
                """)
                
                result = await session.execute(query, {
                    "property_id": property_id, 
                    "tenant_id": tenant_id
                })
                row = result.fetchone()
                
                if row:
                    total_revenue = Decimal(str(row.total_revenue))
                    return {
                        "property_id": property_id,
                        "tenant_id": tenant_id,
                        "total": str(total_revenue),
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
        # FIX: Was falling back to hardcoded mock data that silently masked DB failures.
        # The mock for prop-001 was wrong (1000.00 instead of 2250.00), causing the bug
        # reported by Client A. Now the error propagates and surfaces as HTTP 500.
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        raise