from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Dict, Any, List, Optional
from ...services.cache import get_revenue_summary
from ...core.auth import authenticate_request as get_current_user
from ...database import supabase
from ...models.auth import AuthenticatedUser
from pydantic import BaseModel

router = APIRouter()

class Property(BaseModel):
    id: str
    name: str

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = current_user.tenant_id or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    total_revenue_float = float(revenue_data['total'])
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": total_revenue_float,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }

@router.get("/dashboard/properties")
async def get_dashboard_properties(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, List[Property]]:
    try:
        tenant_id = current_user.tenant_id
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant ID is missing")

        # Select columns available in the table
        query = supabase.table('properties').select('id, name, tenant_id').eq('status', 'active')
        
        # Filter by tenant_id
        query = query.eq('tenant_id', tenant_id)

        # Execute query
        result = query.execute()
        
        properties = []
        
        # Handle MoveResponse object if relevant
        data = result.data if hasattr(result, 'data') else []
        if isinstance(data, list):
             for row in data:
                properties.append(Property(
                    id=row['id'],
                    name=row['name']
                ))
            
        return {"properties": properties}

    except Exception as e:
        print(f"Error fetching dashboard properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))
