from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    # If month/year specified, use monthly calculation
    if month and year:
        from app.services.reservations import calculate_monthly_revenue, calculate_monthly_reservation_count
        from app.core.database_pool import db_pool
        
        # Get property timezone from database
        async with db_pool.get_session() as session:
            from sqlalchemy import text
            query = text("SELECT timezone FROM properties WHERE id = :property_id AND tenant_id = :tenant_id")
            result = await session.execute(query, {"property_id": property_id, "tenant_id": tenant_id})
            row = result.fetchone()
            property_timezone = row.timezone if row else "UTC"
        
        # Calculate both revenue and count for the month
        monthly_total = await calculate_monthly_revenue(property_id, tenant_id, month, year, property_timezone)
        monthly_count = await calculate_monthly_reservation_count(property_id, tenant_id, month, year, property_timezone)
        
        return {
            "property_id": property_id,
            "total_revenue": str(monthly_total),
            "currency": "USD",
            "reservations_count": monthly_count,
            "period": f"{year}-{month:02d}",
            "timezone": property_timezone
        }
    
    # Default: return total revenue
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
