from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import dashboard as dashboard_module
from app.core.auth import authenticate_request as get_current_user


def _build_test_client(user_obj):
    app = FastAPI()
    app.include_router(dashboard_module.router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: user_obj
    return TestClient(app)


def test_dashboard_summary_uses_authenticated_tenant(monkeypatch):
    captured = {}

    async def fake_get_revenue_summary(property_id: str, tenant_id: str):
        captured["property_id"] = property_id
        captured["tenant_id"] = tenant_id
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": "123.45",
            "currency": "USD",
            "count": 2,
        }

    monkeypatch.setattr(dashboard_module, "get_revenue_summary", fake_get_revenue_summary)

    client = _build_test_client(SimpleNamespace(tenant_id="tenant-a"))
    response = client.get("/api/v1/dashboard/summary", params={"property_id": "prop-1"})

    assert response.status_code == 200
    assert response.json()["property_id"] == "prop-1"
    assert response.json()["total_revenue"] == 123.45
    assert captured == {"property_id": "prop-1", "tenant_id": "tenant-a"}


def test_dashboard_summary_rejects_missing_tenant(monkeypatch):
    called = {"value": False}

    async def fake_get_revenue_summary(property_id: str, tenant_id: str):
        called["value"] = True
        return {
            "property_id": property_id,
            "tenant_id": tenant_id,
            "total": "0.00",
            "currency": "USD",
            "count": 0,
        }

    monkeypatch.setattr(dashboard_module, "get_revenue_summary", fake_get_revenue_summary)

    client = _build_test_client(SimpleNamespace(tenant_id=None))
    response = client.get("/api/v1/dashboard/summary", params={"property_id": "prop-1"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Tenant context is required"
    assert called["value"] is False
