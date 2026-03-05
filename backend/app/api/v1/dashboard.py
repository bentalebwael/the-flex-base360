from fastapi import APIRouter, Depends
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from sqlalchemy import text
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import db_pool

router = APIRouter()


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"

    await db_pool.initialize()
    if not db_pool.session_factory:
        return []

    async with db_pool.get_session() as session:
        query = text(
            """
            SELECT id, name, timezone
            FROM properties
            WHERE tenant_id = :tenant_id
            ORDER BY name ASC, id ASC
            """
        )
        result = await session.execute(query, {"tenant_id": tenant_id})
        rows = result.fetchall()

    return [
        {"id": row.id, "name": row.name, "timezone": row.timezone}
        for row in rows
    ]


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    month: int | None = None,
    year: int | None = None,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(
        property_id,
        tenant_id,
        month=month,
        year=year,
    )
    
    try:
        total_revenue_decimal = Decimal(str(revenue_data["total"])).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError):
        total_revenue_decimal = Decimal("0.00")
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": format(total_revenue_decimal, "f"),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
        "report_month": revenue_data.get("report_month"),
        "report_year": revenue_data.get("report_year"),
        "property_timezone": revenue_data.get("property_timezone"),
    }
