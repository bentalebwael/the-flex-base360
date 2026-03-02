from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    import os
    challenge_mode = os.getenv("CHALLENGE_MODE", "1") == "1"
    simulated_tenant = request.headers.get("X-Simulated-Tenant")
    tenant_id = simulated_tenant if (challenge_mode and simulated_tenant) else getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    try:
        revenue_data = await get_revenue_summary(property_id, tenant_id)
        total_revenue_float = float(revenue_data['total'])
        return {
            "property_id": revenue_data['property_id'],
            "total_revenue": total_revenue_float,
            "currency": revenue_data['currency'],
            "reservations_count": revenue_data['count']
        }
    except Exception as e:
        import logging
        logging.error(f"Failed to load revenue data for property_id={property_id}, tenant_id={tenant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load revenue data: {str(e)}")
