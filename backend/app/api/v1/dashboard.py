from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()


async def verify_property_access(property_id: str, tenant_id: str) -> bool:
    """
    Verifies that the property belongs to the given tenant.
    Returns True if the property exists and belongs to the tenant, False otherwise.
    """
    try:
        from app.core.database_pool import db_pool
        from sqlalchemy import text
        
        if not db_pool.session_factory:
            await db_pool.initialize()
        
        async with db_pool.get_session() as session:
            query = text("""
                SELECT 1 FROM properties 
                WHERE id = :property_id AND tenant_id = :tenant_id
            """)
            result = await session.execute(query, {
                "property_id": property_id,
                "tenant_id": tenant_id
            })
            return result.fetchone() is not None
    except Exception as e:
        print(f"Error verifying property access: {e}")
        return False


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    # Verify the user has access to this property
    has_access = await verify_property_access(property_id, tenant_id)
    if not has_access:
        raise HTTPException(status_code=403, detail="You do not have access to this property")
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue = revenue_data['total']
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
