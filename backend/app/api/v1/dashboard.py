from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
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

    total_revenue = float(Decimal(revenue_data['total']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


@router.get("/dashboard/properties")
async def get_tenant_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Returns only the properties belonging to the authenticated tenant."""

    tenant_id = getattr(current_user, "tenant_id", None) or "default_tenant"

    try:
        import asyncpg
        from app.config import settings

        db_url = settings.database_url.replace("postgresql://", "postgresql://", 1)
        conn = await asyncpg.connect(db_url)
        try:
            rows = await conn.fetch(
                "SELECT id, name FROM properties WHERE tenant_id = $1 ORDER BY id",
                tenant_id,
            )
            return [{"id": row["id"], "name": row["name"]} for row in rows]
        finally:
            await conn.close()

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not load properties: {e}")
