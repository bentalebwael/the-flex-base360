from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.services.reservations import calculate_total_revenue
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: int | None = Query(default=None, ge=1, le=12),
    year: int | None = Query(default=None, ge=2000, le=2100),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required")

    if (month is None) != (year is None):
        raise HTTPException(status_code=400, detail="month and year must be provided together")

    if month is not None and year is not None:
        # Monthly requests are computed directly (timezone-aware) and intentionally uncached.
        revenue_data = await calculate_total_revenue(property_id, tenant_id, month=month, year=year)
    else:
        # All-time summary can use cache.
        revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
