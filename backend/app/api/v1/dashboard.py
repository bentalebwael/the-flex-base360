from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:

    # Fail-closed on missing tenant. The previous `"default_tenant"` fallback would
    # silently turn an auth/tenant-resolution bug into a request for a nonexistent
    # tenant, which returns zeroes — a misleading success. 401 surfaces the problem.
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Authenticated user missing tenant_id")

    # month+year must be paired; reject half-specified queries early
    if (month is None) != (year is None):
        raise HTTPException(
            status_code=400,
            detail="`month` and `year` must be provided together (or both omitted for all-time).",
        )

    try:
        revenue_data = await get_revenue_summary(property_id, tenant_id, month=month, year=year)
    except ValueError as e:
        # Service-layer ValueError signals a detected data-state issue (e.g. the
        # multi-currency case) — surface as 409 Conflict, not a 500 with a traceback.
        raise HTTPException(status_code=409, detail=str(e))

    # total_revenue is returned as a string to preserve NUMERIC(10,3) precision.
    # Casting to float here used to introduce IEEE-754 drift, compounded by the
    # frontend's Math.round(x * 100) / 100 which silently truncated the mills digit.
    # Keeping the value as a string all the way to the renderer is the preventive
    # form of the fix: no binary float ever touches the number, and the TypeScript
    # type on the frontend rejects any accidental arithmetic on it.
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
        "month": month,
        "year": year,
    }
