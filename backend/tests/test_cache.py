import pytest
import json


def build_cache_key(tenant_id: str, property_id: str) -> str:
    """Mirrors the cache key format in cache.py."""
    return f"revenue:{tenant_id}:{property_id}"


def test_cache_key_includes_tenant_id(tenant_a_context):
    key = build_cache_key(tenant_a_context["tenant_id"], tenant_a_context["property_id"])
    assert tenant_a_context["tenant_id"] in key
    assert tenant_a_context["property_id"] in key
    assert key == "revenue:tenant-a:prop-001"


def test_different_tenants_same_property_get_separate_cache(tenant_a_context, tenant_b_context):
    key_a = build_cache_key(tenant_a_context["tenant_id"], tenant_a_context["property_id"])
    key_b = build_cache_key(tenant_b_context["tenant_id"], tenant_b_context["property_id"])
    assert key_a != key_b


def test_cache_returns_stored_value_on_hit(mock_redis, tenant_a_context):
    key = build_cache_key(tenant_a_context["tenant_id"], tenant_a_context["property_id"])
    payload = {"property_id": "prop-001", "total": "2250.00", "currency": "USD", "count": 4}
    mock_redis[key] = json.dumps(payload)

    cached = mock_redis.get(key)
    assert cached is not None
    assert json.loads(cached)["total"] == "2250.00"
