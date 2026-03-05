from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from sqlalchemy import text
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import db_pool

router = APIRouter()


def _format_money(value: Any) -> str:
    try:
        amount = Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal("0.00")
    return format(amount, "f")


def _format_percentage(value: Any) -> str | None:
    if value is None:
        return None
    try:
        pct = Decimal(str(value)).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, TypeError, ValueError):
        return None
    return format(pct, "f")


def _require_tenant_id(current_user: Any) -> str:
    tenant_id = getattr(current_user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context is required for dashboard access",
        )
    return tenant_id


@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    tenant_id = _require_tenant_id(current_user)

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
    tenant_id = _require_tenant_id(current_user)

    revenue_data = await get_revenue_summary(
        property_id,
        tenant_id,
        month=month,
        year=year,
    )
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": _format_money(revenue_data.get("total")),
        "total_revenue_all_time": _format_money(revenue_data.get("total_all_time")),
        "previous_month_revenue": _format_money(revenue_data.get("previous_month_total")),
        "revenue_change_percent": _format_percentage(
            revenue_data.get("revenue_change_percent")
        ),
        "revenue_trend_direction": revenue_data.get("revenue_trend_direction"),
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count'],
        "report_month": revenue_data.get("report_month"),
        "report_year": revenue_data.get("report_year"),
        "property_timezone": revenue_data.get("property_timezone"),
    }
