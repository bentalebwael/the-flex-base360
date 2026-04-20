from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:

    # Fail-closed: a missing tenant_id used to fall back to the literal string
    # "default_tenant", which then runs the revenue query against a tenant
    # that doesn't exist (returning 0 rows + currently masked by the mock
    # fallback). Refuse the request instead.
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No tenant associated with this user",
        )

    revenue_data = await get_revenue_summary(property_id, tenant_id)

    # Pass total as string to preserve Decimal precision. total_amount is
    # NUMERIC(10,3) — converting to float introduces IEEE-754 rounding that
    # showed up as the "off by a few cents" complaint from finance.
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
    }
