from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from datetime import datetime
from dateutil.relativedelta import relativedelta

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    year: int,
    month: int,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Invalid tenant context")
    
    start_date = datetime(year, month, 1)
    end_date = start_date + relativedelta(months=1)

    revenue_data = await get_revenue_summary(
        property_id, 
        tenant_id, start_date, end_date
    )
        )
    
    # total_revenue_float = float(revenue_data['total'])

    # total_revenue_float = Decimal(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
