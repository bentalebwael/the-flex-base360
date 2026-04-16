import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import DatabasePool
from app.models.auth import AuthenticatedUser
from app.services.cache import get_revenue_summary

logger = logging.getLogger(__name__)
router = APIRouter()

_PROPERTIES_SQL = text(
    """
    SELECT id, name
    FROM properties
    WHERE tenant_id = :tenant_id
    ORDER BY name
    """
)


def _tenant_from_user(user: AuthenticatedUser) -> str:
    return user.tenant_id or "default_tenant"


@router.get("/dashboard/properties")
async def list_dashboard_properties(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> List[Dict[str, str]]:
    """Properties visible to this login (scoped by tenant)."""
    tenant_id = _tenant_from_user(current_user)
    pool = DatabasePool()
    try:
        await pool.initialize()
        if not pool.session_factory:
            logger.warning("Dashboard properties: pool not ready for tenant %s", tenant_id)
            return []
        async with pool.get_session() as session:
            result = await session.execute(_PROPERTIES_SQL, {"tenant_id": tenant_id})
            records = result.fetchall()
            return [{"id": r.id, "name": r.name} for r in records]
    except Exception:
        logger.exception("Dashboard properties query failed (tenant=%s)", tenant_id)
        return []


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    tenant_id = _tenant_from_user(current_user)
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
