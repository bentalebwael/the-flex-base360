from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    # Never convert financial values to float.
    # Previously: total_revenue_float = float(revenue_data['total'])
    # float() causes two problems:
    #   1. Binary imprecision: float('333.333') = 333.33300000000002683009
    #   2. Trailing zeros stripped: float('4975.500') = 4975.5
    #      This causes display mismatches vs. client accounting systems.
    # Solution: return the value as a string; the frontend formats display.
    total_revenue_str = str(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_str,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
