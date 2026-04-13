from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    year: Optional[int] = Query(None, ge=2000, le=2100),
    month: Optional[int] = Query(None, ge=1, le=12),
    current_user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    if (year is None) ^ (month is None):
        raise HTTPException(
            status_code=400,
            detail="Provide both year and month for a period filter, or omit both for all-time totals.",
        )
    
    revenue_data = await get_revenue_summary(
        property_id, tenant_id, year=year, month=month
    )

    total_revenue_float = float(
        Decimal(str(revenue_data["total"])).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
    )
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
        "period": {"year": year, "month": month} if year is not None else None,
    }
