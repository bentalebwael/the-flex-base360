from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from sqlalchemy import text

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # get tenant id for the current user
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    # fetch data from service
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    if revenue_data is None:
        # get null fake data if try to get the other's data
        return {
            "property_id": property_id,
            "total_revenue": 0.0,
            "currency": "USD",
            "reservations_count": 0
        }
    
    total_revenue_float = float(revenue_data.get('total', 0))
    
    return {
        "property_id": revenue_data.get('property_id', property_id),
        "total_revenue": total_revenue_float,
        "currency": revenue_data.get('currency', 'USD'),
        "reservations_count": revenue_data.get('count', 0)
    }

#to get current user's properties not hardcoded
@router.get("/properties/list")
async def list_properties(current_user: dict = Depends(get_current_user)):
    #get tenant id for current user login
    tenant_id = getattr(current_user, "tenant_id", "default_tenant")

    from app.core.database_pool import DatabasePool
    db_pool = DatabasePool()
    await db_pool.initialize()
    
    if not db_pool.session_factory:
        raise HTTPException(status_code=500, detail="Database pool not available")

    # query to get current user's properties
    async with db_pool.get_session() as session:
        query = text("""
            SELECT id, name 
            FROM properties 
            WHERE tenant_id = :tenant_id
        """)
        
        result = await session.execute(query, {"tenant_id": tenant_id})
        rows = result.fetchall()
        
        # get result as list
        return [{"id": row.id, "name": row.name} for row in rows]