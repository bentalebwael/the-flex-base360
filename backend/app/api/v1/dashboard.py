from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()


@router.get("/dashboard/properties")
async def get_tenant_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, str]]:
    """Return properties belonging to the authenticated user's tenant."""
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    try:
        from app.core.database_pool import DatabasePool
        from sqlalchemy import text

        db_pool = DatabasePool()
        await db_pool.initialize()

        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                result = await session.execute(
                    text("SELECT id, name FROM properties WHERE tenant_id = :tid ORDER BY name"),
                    {"tid": tenant_id},
                )
                rows = result.fetchall()
                return [{"id": row.id, "name": row.name} for row in rows]

        raise Exception("Database pool not available")

    except Exception as e:
        print(f"Error fetching properties for tenant {tenant_id}: {e}")
        return []


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)

    # ⚠️ [BUG 3 - FIX: Floating-Point Precision]
    # BEFORE: total_revenue_float = float(revenue_data['total'])  ← float 변환으로 정밀도 손실
    # PROBLEM: 333.333 + 333.333 + 333.334 = 1000.000이어야 하지만 float 변환 시 센트 오차 발생
    # FIX: Decimal/string 값을 그대로 유지하거나 round(Decimal(...), 2)로 정밀하게 반올림
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
