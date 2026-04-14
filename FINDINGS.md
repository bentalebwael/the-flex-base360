# Bug Fix Findings

## Bug 1: Cross-Tenant Data Leakage (Privacy)

- **File patched:** `backend/app/services/cache.py`
- **Line changed:** 13
- **Before:** `cache_key = f"revenue:{property_id}"`
- **After:** `cache_key = f"revenue:{tenant_id}:{property_id}"`
- **Root Cause:** Cache key only used `property_id`, so different tenants sharing the same property ID would get each other's cached revenue data.
- **Verification:** Client B no longer sees Client A's data on refresh. Each tenant's cache is isolated by `tenant_id`.

---

## Bug 2: Revenue Precision Loss (Floating Point Drift)

- **File patched:** `backend/app/api/v1/dashboard.py`
- **Line changed:** 18
- **Before:** `total_revenue_float = float(revenue_data['total'])` then returned `total_revenue_float`
- **After:** Directly returns `revenue_data['total']` (string representation of exact Decimal value)
- **Root Cause:** Converting Decimal/string to `float()` introduced IEEE 754 floating-point errors (e.g., `4975.50` could become `4975.4999999...`).
- **Verification:** Revenue totals now match DB `NUMERIC(10,3)` values exactly, with no cent-level discrepancies.

---

## Bug 3: Timezone-Unaware Monthly Revenue Boundaries

- **File patched:** `backend/app/services/reservations.py`
- **Lines changed:** 1-32 (added `ZoneInfo` import, timezone lookup, timezone-aware datetime boundaries)
- **Before:** `start_date = datetime(year, month, 1)` — naive UTC datetime
- **After:** Fetches property timezone from DB, creates timezone-aware boundaries: `start_date = datetime(year, month, 1, tzinfo=property_tz)`
- **Root Cause:** Month boundaries were calculated in UTC, but properties have local timezones (e.g., `Europe/Paris`, `America/New_York`). A reservation at `2024-02-29T23:30Z` is actually March 1st in Paris, but was counted as February revenue.
- **Verification:** Client A (Sunset Properties, Europe/Paris) March totals now correctly include reservations that fall in March local time.
