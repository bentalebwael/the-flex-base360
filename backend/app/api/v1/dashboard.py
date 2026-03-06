from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    # استخراج الـ tenant_id بأمان
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    # جلب البيانات من السيرفس
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    # --- تعديل الحماية هنا ---
    if revenue_data is None:
        # لو مفيش بيانات، رجع قيم افتراضية بدل ما الـ App يضرب
        return {
            "property_id": property_id,
            "total_revenue": 0.0,
            "currency": "USD",
            "reservations_count": 0
        }
    
    # لو البيانات موجودة، حولها لـ float زي ما كنت عايز
    total_revenue_float = float(revenue_data.get('total', 0))
    
    return {
        "property_id": revenue_data.get('property_id', property_id),
        "total_revenue": total_revenue_float,
        "currency": revenue_data.get('currency', 'USD'),
        "reservations_count": revenue_data.get('count', 0)
    }
