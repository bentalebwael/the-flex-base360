from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.services.revenue_format import format_revenue_total
from app.services.properties import list_tenant_properties
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    try:
        revenue_data = await get_revenue_summary(property_id, tenant_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Revenue data unavailable") from exc

    if revenue_data is None:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": format_revenue_total(revenue_data['total']),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")

    try:
        properties = await list_tenant_properties(tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Property list unavailable") from exc

    return {"properties": properties}
