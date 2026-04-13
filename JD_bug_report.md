# Bug Fix Report: Rifat

## Observations (Not necessarily bad ones only)

1. Docker build worked fine, no issues.
2. Both client logins worked.
3. Both clients see identical property lists and revenue numbers — clear sign of a data isolation problem.
4. Profile links are broken but unrelated to the reported issues.


## Bug 1: Cross-tenant data leak (Client B)

**Complaint:** Ocean Rentals occasionally sees another company's revenue data.

**Cause 1:** Cache key in `cache.py` only used `property_id`. Both tenants have `prop-001`, so they shared the same cache entry.

**Fix:** `backend/app/services/cache.py`
```python
# Before
cache_key = f"revenue:{property_id}"
# After
cache_key = f"revenue:{tenant_id}:{property_id}"
```

**Cause 2:** The database pool in `database_pool.py` always failed to initialize due to three bugs, causing every request to fall back to mock data that had no tenant filtering. Three fixes applied:

> Disclaimer: some specific issues here were identified and fixed with the help of Claude

**Fix:** `backend/app/core/database_pool.py`
```python
# Fix 1: Wrong settings attributes
database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fix 2: QueuePool is incompatible with async engine, removed it (identified and done by Claude)
self.engine = create_async_engine(database_url, pool_size=20, ...)

# Fix 3: Removed async from get_session() so it returns a session (identified and done by Claude)
def get_session(self) -> AsyncSession:
```



## Bug 2: Floating-point precision (Finance team)

**Complaint:** Revenue totals off by a few cents.

**Cause:** `float()` conversion on amounts like `333.333 + 333.333 + 333.334` produces binary imprecision (e.g. `999.9999999999`).

**Fix:** `backend/app/api/v1/dashboard.py`
```python
# Before
total_revenue_float = float(revenue_data['total'])
# After
total_revenue_float = float(Decimal(str(revenue_data['total'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
```



## Bug 3: Timezone mismatch (Client A)

**Complaint:** Sunset Properties' March revenue doesn't match internal records.

**Cause:** `calculate_monthly_revenue` used naive `datetime` objects (no timezone), so March boundaries were treated as UTC. Reservation `res-tz-1` has `check_in_date = 2024-02-29 23:30:00+00` (UTC), which is March 1 00:30 in `Europe/Paris` (where `prop-001` is located) — but the UTC boundary excluded it from March, dropping $1,250 from the total. The function also never actually queried the DB (always returned `Decimal('0')`).

**Fix:** `backend/app/services/reservations.py`
```python
# Reads property timezone from DB, builds boundaries in local time, converts to UTC
property_tz = ZoneInfo(tz_row.timezone)
start_local = datetime(year, month, 1, tzinfo=property_tz)
start_utc = start_local.astimezone(timezone.utc)
# Then queries DB with the correct UTC range
```

Also added `GET /dashboard/monthly?property_id=&month=&year=` endpoint in `backend/app/api/v1/dashboard.py` to make this testable via Swagger.
