from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: int | None = None,
    year: int | None = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:

    tenant_id = getattr(current_user, "tenant_id", "")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="No tenant ID is found.")

    if (month is None) != (year is None):
        raise HTTPException(status_code=400, detail="Both month and year must be provided together.")
    if month is not None and (month < 1 or month > 12):
        raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")
    
    revenue_data = await get_revenue_summary(property_id, tenant_id, month=month, year=year)

    total_revenue_float = float(
        Decimal(str(revenue_data["total"]))
        .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
