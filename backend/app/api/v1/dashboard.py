from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime, timezone
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
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    # OLD (kept for reference):
    # revenue_data = await get_revenue_summary(property_id, tenant_id)
    now = datetime.now(timezone.utc)
    selected_month = month or now.month
    selected_year = year or now.year
    revenue_data = await get_revenue_summary(
        property_id,
        tenant_id,
        selected_month,
        selected_year,
    )
    
    # OLD (kept for reference):
    # total_revenue_float = float(revenue_data['total'])
    total_revenue_decimal = str(revenue_data["total"])
    total_revenue_display = str(
        Decimal(total_revenue_decimal).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    )
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_decimal,
        "total_revenue_display": total_revenue_display,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
        "month": selected_month,
        "year": selected_year,
    }
