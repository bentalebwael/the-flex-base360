from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP
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

    # FIX BUG 3: DECIMAL PRECISION - Avoid float conversion that introduces rounding errors
    # Previously: total_revenue_float = float(revenue_data['total']) caused issues like
    # 333.333 + 333.333 + 333.334 becoming 1000.00000001 instead of exactly 1000.00
    # Now we use Decimal for precise financial calculations and round to 2 decimal places
    total_decimal = Decimal(str(revenue_data['total']))
    total_revenue_rounded = float(total_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_rounded,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
