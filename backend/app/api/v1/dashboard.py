from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from app.services.cache import get_revenue_summary
from app.services.reservations import calculate_monthly_revenue
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/monthly")
async def get_monthly_revenue(
    property_id: str,
    month: int,
    year: int,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns revenue for a specific month, bucketed by the property's local timezone.
    Use this to verify the timezone fix: prop-001 (Europe/Paris) should include
    reservation res-tz-1 (2024-02-29 23:30 UTC = 2024-03-01 00:30 Paris) in March 2024.
    """
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month must be between 1 and 12")

    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    total = await calculate_monthly_revenue(property_id, tenant_id, month, year)
    total_rounded = float(Decimal(str(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    return {
        "property_id": property_id,
        "month": month,
        "year": year,
        "total_revenue": total_rounded,
        "currency": "USD",
    }

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)

    # Before:
    # total_revenue_float = float(revenue_data['total'])
    
    #Fix: Use Decimal for accurate rounding to 2 decimal places
    total_revenue_float = float(Decimal(str(revenue_data['total'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
