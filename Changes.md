# Changes

## Bug 1 — Cross-tenant cache leak (`backend/app/services/cache.py`)

**Symptom:** Ocean Rentals (tenant-b) was seeing revenue numbers belonging to Sunset Properties (tenant-a).

**Root cause:** The Redis cache key was `revenue:{property_id}`, with no tenant segment. Both tenants happen to share the property ID `prop-001` (Beach House Alpha for tenant-a, Mountain Lodge Beta for tenant-b). When tenant-a's data was cached first, any subsequent request for `prop-001` — regardless of tenant — returned tenant-a's figures.

**Fix:** Added `tenant_id` to the cache key: `revenue:{property_id}:{tenant_id}`.

---

## Bug 2 — Revenue query bypassed tenant isolation (`backend/app/services/reservations.py`)

**Symptom:** Even after flushing Redis, Mountain Lodge Beta (tenant-b / `prop-001`) still showed ~$1,000 and 3 bookings — the exact figures belonging to Beach House Alpha (tenant-a / `prop-001`).

**Root cause:** `calculate_total_revenue` attempted to use `DatabasePool`, which always failed silently because it tried to read non-existent `settings.supabase_db_*` config fields. The exception handler returned **hardcoded mock data keyed only by `property_id`**, so `prop-001` always yielded `{total: "1000.00", count: 3}` for every tenant.

**Fix:** Replaced the broken `DatabasePool` path and the mock fallback with a direct `asyncpg` query that filters by both `property_id` and `tenant_id`.

---

## Bug 3 — Sub-cent amounts producing penny-rounding discrepancies (`backend/app/api/v1/dashboard.py`, `database/schema.sql`)

**Symptom:** Finance team noticed revenue totals were off by a few cents.

**Root cause (data model):** `total_amount` is stored as `NUMERIC(10, 3)` — three decimal places. The seed data for Beach House Alpha contains three reservations at `333.333`, `333.333`, and `333.334`. Each displays as `$333.33` when rounded to cents, so the finance team manually sums `$333.33 × 3 = $999.99`. The DB `SUM` is `$1000.000`, which rounds to `$1000.00` — a $0.01 discrepancy.

**Root cause (API layer):** The original code did `float(revenue_data['total'])`, converting a `Decimal` string to a Python `float` (IEEE-754), which can introduce its own rounding errors and also returns the raw sub-cent total without normalising to cents. The intermediate "fix" of removing the cast changed the return type from a JSON number to a JSON string, mismatching the TypeScript `number` interface.

**Fix:** Parse as `Decimal`, quantize to 2 decimal places with `ROUND_HALF_UP` (standard financial rounding), then convert to `float` so the JSON response remains a number and matches the frontend type:
```python
total_revenue = float(
    Decimal(revenue_data['total']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
)
```

**Note:** The schema storing `NUMERIC(10, 3)` is a design decision. If sub-cent precision is not required, changing the column to `NUMERIC(10, 2)` would eliminate the root cause entirely.

---

## Bug 4 — Hardcoded property list exposed all tenants' properties (`frontend/src/components/Dashboard.tsx` + `backend/app/api/v1/properties.py` + `backend/app/main.py`)

**Symptom:** Every logged-in user could see and select properties belonging to other tenants (all five properties from both tenants were always shown).

**Root cause:** `Dashboard.tsx` rendered a hardcoded `PROPERTIES` array containing every property in the system, with no relation to the authenticated user's tenant.

**Fix:**
- Created `GET /api/v1/properties` endpoint (`properties.py`) that queries the database for properties filtered by the authenticated user's `tenant_id`.
- Registered the new router in `main.py`.
- Updated `Dashboard.tsx` to fetch the property list dynamically on mount via `SecureAPI.getProperties()` instead of using the hardcoded array.
