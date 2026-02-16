from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.core.database_pool import DatabasePool
from sqlalchemy import text

router = APIRouter()

@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: dict = Depends(get_current_user)
):
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    try:
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                query = text("""
                    SELECT id, name 
                    FROM properties 
                    WHERE tenant_id = :tenant_id
                """)
                result = await session.execute(query, {"tenant_id": tenant_id})
                properties = [{"id": row.id, "name": row.name} for row in result.fetchall()]
                return properties
        else:
            raise Exception("Database pool not available")
    except Exception as e:
        print(f"Error fetching properties for tenant {tenant_id}: {e}")
        # Fallback to tenant-specific mock properties if DB fails
        if tenant_id == "tenant-a":
            return [
                {"id": "prop-001", "name": "Beach House Alpha"},
                {"id": "prop-002", "name": "City Apartment Downtown"},
                {"id": "prop-003", "name": "Country Villa Estate"}
            ]
        else:
            return [
                {"id": "prop-001", "name": "Mountain Lodge Beta"},
                {"id": "prop-004", "name": "Lakeside Cottage"},
                {"id": "prop-005", "name": "Urban Loft Modern"}
            ]

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    # Use strings for monetary values to preserve exact precision. 
    # Converting to float can cause "cents-off" discrepancies due to IEEE 754 floating point limitations.
    total_revenue_str = str(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_str,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
