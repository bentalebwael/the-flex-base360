"""
Bug #1: cache key in services/cache.py is not scoped to the tenant.

Current key:  revenue:{property_id}
Fixed key:    revenue:{tenant_id}:{property_id}

prop-001 exists in BOTH tenant-a (Beach House Alpha) and tenant-b
(Mountain Lodge Beta) — see seed.sql. Whichever tenant loads the
dashboard first caches the result under the bare property key; the
other tenant then reads that wrong data, leaking one client's revenue
figures to another. This is the privacy violation reported by Client B.
"""
import json


PROP_ID   = "prop-001"
TENANT_A  = "tenant-a"
TENANT_B  = "tenant-b"

TENANT_A_REVENUE = {
    "property_id": PROP_ID, "tenant_id": TENANT_A,
    "total": "2250.00", "currency": "USD", "count": 4,
}
TENANT_B_REVENUE = {
    "property_id": PROP_ID, "tenant_id": TENANT_B,
    "total": "750.00", "currency": "USD", "count": 2,
}


# ── mirror current and fixed key construction ─────────────────────────────

def current_key(property_id: str, tenant_id: str) -> str:
    """Reproduces cache.py line 13: f'revenue:{property_id}'"""
    return f"revenue:{property_id}"


def fixed_key(property_id: str, tenant_id: str) -> str:
    """Fixed: include tenant_id so each tenant has its own entry."""
    return f"revenue:{tenant_id}:{property_id}"


# ── tests ─────────────────────────────────────────────────────────────────

def test_buggy_key_collides_for_shared_property_id():
    """
    The same property ID (prop-001) belongs to both tenants in seed.sql.
    The buggy key maps both tenants to the same cache slot.
    """
    assert current_key(PROP_ID, TENANT_A) == current_key(PROP_ID, TENANT_B)


def test_fixed_key_produces_distinct_slot_per_tenant():
    """Fixed key generates a unique entry per (tenant, property) pair."""
    assert fixed_key(PROP_ID, TENANT_A) != fixed_key(PROP_ID, TENANT_B)


def test_buggy_key_leaks_tenant_a_revenue_to_tenant_b():
    """
    Reproduce the Client B complaint:
      1. Tenant-a loads dashboard → cache miss → stores result.
      2. Tenant-b loads dashboard → cache hit → receives tenant-a's data.
    """
    cache: dict[str, str] = {}

    # Tenant-a: miss → compute → store
    cache[current_key(PROP_ID, TENANT_A)] = json.dumps(TENANT_A_REVENUE)

    # Tenant-b: should miss, but collides with tenant-a's key
    hit = cache.get(current_key(PROP_ID, TENANT_B))
    assert hit is not None, "Tenant-b should not get a cache hit — but it does (the bug)"

    leaked = json.loads(hit)
    assert leaked["tenant_id"] == TENANT_A   # wrong tenant's data
    assert leaked["total"] == "2250.00"       # tenant-a's revenue, not tenant-b's 750.00


def test_fixed_key_tenant_b_gets_cache_miss():
    """
    With the fix, tenant-b's lookup finds nothing in cache after
    tenant-a has populated it — each tenant fetches its own data.
    """
    cache: dict[str, str] = {}

    # Tenant-a populates cache with the fixed key
    cache[fixed_key(PROP_ID, TENANT_A)] = json.dumps(TENANT_A_REVENUE)

    # Tenant-b looks up their own fixed key → miss → safe
    hit = cache.get(fixed_key(PROP_ID, TENANT_B))
    assert hit is None, "Tenant-b must get a cache miss with the fixed key"


def test_fixed_key_both_tenants_see_correct_data():
    """Both tenants can coexist in cache without collision after the fix."""
    cache: dict[str, str] = {}

    cache[fixed_key(PROP_ID, TENANT_A)] = json.dumps(TENANT_A_REVENUE)
    cache[fixed_key(PROP_ID, TENANT_B)] = json.dumps(TENANT_B_REVENUE)

    result_a = json.loads(cache[fixed_key(PROP_ID, TENANT_A)])
    result_b = json.loads(cache[fixed_key(PROP_ID, TENANT_B)])

    assert result_a["tenant_id"] == TENANT_A and result_a["total"] == "2250.00"
    assert result_b["tenant_id"] == TENANT_B and result_b["total"] == "750.00"
