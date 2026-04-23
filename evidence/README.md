# Evidence — before/after captures for the Loom demo

Git-ignored. Captured in three phases keyed to the fix plan:

- **Phase 1** — current broken-out-of-the-box state (mock fallback confounding everything). ✅ captured.
- **Phase 2A** — clean "before" shots for Bugs 1 / 2 / 6 / 7. Only capturable in the narrow window **after Step 0 lands** (mock gone, real DB flows) but **before** any of those fixes. Miss this window → have to roll fixes back to re-capture.
- **Phase 2B** — "after" shots for each fix. Captured incrementally as each bug is resolved.

## Phase 1 ✅ (captured)

### Shared
- `db-truth.txt` — real DB sums per (property, tenant). Source of truth for every "before" API response.
- `planted-test-rows.txt` — the four planted rows (`res-tz-1`, `res-dec-1/2/3`).
- `property-tenant-mapping.txt` — `prop-001` on both tenants (different names + timezones).

### `prereq/` — Bug 3a, Bug 5, Bug 3b
- `backend-logs-mock-firing.txt` — `'Settings' object has no attribute 'supabase_db_user'` + `Database pool not available` + subsequent `Database error for prop-001`.
- `login-response-clientA-redacted.json`, `login-response-clientB-redacted.json` — successful logins; tokens replaced with `<REDACTED>`.
- `dashboard-prop-001-clientA.json` — response `{"total_revenue": 1000.0, "reservations_count": 3}` (matches `mock_data['prop-001']`, NOT the real DB sum of `2250.000 / 4`).
- `dashboard-prop-001-clientB.json` — **identical** response to Client A (same mock firing; also consistent with Bug 1 once the mock is removed).

### `client-a/dashboard-ui-monthly-header.png` — Bug 6 (+ bonus Bug 3b)
Logged in as `sunset@…`, shows:
- "Monthly performance insights for your properties" — the lie.
- "USD 1,000.00 / 3 bookings" for prop-001 — the mock value on-screen.

### `client-b/ocean-property-dropdown.png` — Bug 7 (+ bonus Bug 1)
Logged in as `ocean@…` with the Select Property dropdown open, shows:
- Three tenant-a properties in Ocean Rentals' dropdown: Beach House Alpha, City Apartment Downtown, Country Villa Estate.
- Revenue card behind the dropdown shows the same USD 1,000.00 / 3 bookings for prop-001 (identical to Client A — cache-leak precursor).

### `code-snippets/` — static file:line captures for "code + contradiction" proofs
- `bug-01-cache-key.py` — `cache.py:13` cache key `f"revenue:{property_id}"` without `tenant_id`.
- `bug-02a-float-cast-backend.py` — `dashboard.py:18` `float(revenue_data['total'])`.
- `bug-02b-round-frontend.tsx` — `RevenueSummary.tsx:64` `Math.round(total_revenue * 100) / 100`.
- `bug-03a-bad-db-url.py` — `database_pool.py:18` referencing `settings.supabase_db_user/password/host/port/name`.
- `bug-03b-mock-fallback.py` — the `mock_data` dict in `reservations.py:93-109`.
- `bug-04-tz-naive-month.py` — `calculate_monthly_revenue` using naive `datetime(year, month, 1)`.
- `bug-05-async-session.py` — `async def get_session` plus `async with db_pool.get_session()` caller.
- `bug-06a-ui-monthly-label.tsx` — `Dashboard.tsx:24` "Monthly performance insights".
- `bug-06b-sql-no-month-filter.py` — SQL that sums all reservations, no date predicate.
- `bug-07-hardcoded-properties.tsx` — `Dashboard.tsx:4-10` static `PROPERTIES` array.
- `seed-plants.sql` — full `seed.sql` with the planted rows.

---

## Phase 2A — capture IMMEDIATELY after Step 0 (Bug 3a + 5 + 3b) lands

Narrow window. Mock is gone, real DB flows, but Bugs 1 / 2 / 6 / 7 are still live. Capture all of these in one session before moving on.

| File | Act | Proves | How |
|---|---|---|---|
| `client-b/cache-leak-A-then-B.json` | Client B (Bug 1) | Two curls A-then-B, no flush between — both return `2250.000 / 4` (tenant A's real sum leaking to tenant B). Type-A proof for Bug 1 with no mock to hide behind. | terminal |
| `client-a/all-time-vs-expected-march.txt` | Client A (Bug 6) | API `total_revenue = 2250.000` (all-time) alongside `psql` March-filtered query — quantified mismatch against the "Monthly" UI label. | terminal |
| `finance/res-dec-3-drift.txt` | Finance (Bug 2) | DB `res-dec-3 = 333.334` vs API response after `float()` cast — point-in-point precision loss. | terminal |
| `client-a/dashboard-ui-mock-gone.png` | Client A (Bug 3 after) | Dashboard now displays `USD 2,250.00 / 4 bookings` instead of `1,000.00 / 3` — UI-level proof Step 0 worked. | **browser screenshot (user)** |
| `client-b/dashboard-ui-still-leaking.png` | Client B (Bug 1 UI-level) | Ocean's dashboard shows `USD 2,250.00` for prop-001 — visible leak of tenant A's number to a non-technical viewer. | **browser screenshot (user)** |

## Phase 2B — one "after" capture per remaining fix

Captured incrementally; no window pressure.

| After which fix | File | Shows |
|---|---|---|
| Bug 1 | `client-b/cache-fixed-A-then-B.json` | Same two curls. A=`2250.000`, B=`0`. Tenant B isolated. |
| Bug 6 | `client-a/march-filtered-response.json` | `?month=3&year=2024` returns the correct March total. |
| Bug 4 | `client-a/march-with-tz-included.json` | `res-tz-1` counted in March for tenant-a (Europe/Paris). |
| Bug 7 | `client-b/ocean-dropdown-fixed.png` | Ocean's dropdown only shows their own properties. **browser screenshot (user)** |
| Bug 2 | `finance/res-dec-3-precision-preserved.json` | API preserves Decimal / string `333.334`. No drift. |

## User help summary

- **At Step 0 completion:** two browser screenshots (`client-a/dashboard-ui-mock-gone.png`, `client-b/dashboard-ui-still-leaking.png`).
- **At Bug 7 completion:** one browser screenshot (`client-b/ocean-dropdown-fixed.png`).
- Everything else captured from the terminal.
