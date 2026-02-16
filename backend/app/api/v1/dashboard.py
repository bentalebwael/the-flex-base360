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
    
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="Tenant ID is required for revenue data access"
        )
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_decimal = Decimal(revenue_data['total'])
    quantized_revenue = total_revenue_decimal.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": round(float(quantized_revenue), 2),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
