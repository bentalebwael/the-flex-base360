Architecture

This project has business logic mixed with front-end display (Often can happen as a project grows)
It's a good place to move to feature based architecture, which will help with making it easier to maintain going forward.

/src
  /api
  /features
    /auth
    /dashboard
    /users
  /shared
    /components
    /hooks
    /utils

I'd also suggest implementing Sqitch for database version control

## Senior Developer Change Log (Implementation + Why)

### 2026-04-13 - Step 1 Completed

Change made:
- Updated revenue cache key to include tenant context in [backend/app/services/cache.py](backend/app/services/cache.py).
- Before: `revenue:{property_id}`
- After: `revenue:{tenant_id}:{property_id}`

Why this change:
- Prevents cross-tenant cache collisions where two tenants can share a property ID and accidentally read each other's cached financial summary.
- Directly reduces privacy/compliance risk and addresses the reported “other company numbers after refresh” behavior.
- This is a high-impact, low-risk fix that is safe to ship first.

Risk and impact assessment:
- Risk: Low. Cache namespace change only.
- Impact: High. Tenant isolation is materially improved for dashboard revenue reads.

Validation notes:
- Expected behavior: Cache entries are isolated per tenant and property combination.
- Follow-up validation: login as both tenant users and confirm dashboard totals no longer cross-populate through cache.

### Going Forward (Agreed Process)

For each patch step, update this file with:
- What changed (file + concise technical diff summary)
- Why it changed (security, correctness, performance, maintainability)
- Risk level and expected business impact
- Validation performed or still required

### 2026-04-13 - Step 2 Completed

Change made:
- Updated [backend/app/api/v1/dashboard.py](backend/app/api/v1/dashboard.py) to remove implicit tenant fallback.
- Before: missing tenant defaulted to `default_tenant`.
- After: missing tenant returns HTTP 401 with `Tenant context is required`.

Why this change:
- Failing open with a default tenant can route requests into an unintended tenant context.
- Explicitly requiring tenant context enforces data-boundary correctness at the API edge.
- This complements Step 1 by ensuring tenant-aware cache keys always receive a real tenant ID.

Risk and impact assessment:
- Risk: Low to Medium. Requests with broken auth/tenant metadata now fail fast instead of silently continuing.
- Impact: High. Stronger tenant isolation and clearer auth failure behavior.

Validation notes:
- Expected behavior: authenticated requests with valid tenant_id return dashboard summary; requests without tenant_id return 401.
- Follow-up validation: test with both valid tenant users and a token/session missing tenant metadata.

### 2026-04-13 - Step 3 Completed

Change made:
- Updated [backend/app/core/secure_client.py](backend/app/core/secure_client.py) in `_apply_tenant_filter` for unknown table handling.
- Before: logged warning and returned unfiltered query.
- After: logs error and raises `ValueError` to block unsafe execution.

Why this change:
- Unknown table names are high-risk because the code cannot guarantee tenant scoping.
- Returning unfiltered query is a fail-open pattern that can expose cross-tenant data.
- Raising an error enforces fail-closed behavior and preserves tenant data boundaries.

Risk and impact assessment:
- Risk: Low to Medium. Any call path using unexpected table names will now fail explicitly.
- Impact: High. Removes a latent cross-tenant leakage path and improves security posture.

Validation notes:
- Expected behavior: known tables continue operating as before; unknown tables raise and are handled by calling methods' exception handling.
- Follow-up validation: exercise critical SecureClient paths (`get_properties`, `get_reservations`, `get_tokens`) and verify unknown table paths fail safely.

### Next Planned Step

- Harden [frontend/src/lib/secureApi.ts](frontend/src/lib/secureApi.ts) by removing mock token tenant fallback and strengthening JWT parsing guards.

### 2026-04-13 - Step 4 Completed

Change made:
- Updated [frontend/src/lib/secureApi.ts](frontend/src/lib/secureApi.ts) to remove mock token tenant fallback.
- Added `decodeJwtPayload` helper for safe JWT parsing with malformed token guardrails.
- Refactored tenant ID and session key extraction to use guarded payload decode.

Why this change:
- Static mock-token logic is a security anti-pattern and can create ambiguous tenant context behavior.
- Direct `atob` + `JSON.parse` without guardrails is brittle and can fail noisily with malformed tokens.
- Centralized safe decoding reduces auth edge-case risk and keeps tenant/session derivation deterministic.

Risk and impact assessment:
- Risk: Low. Affects only token parsing paths and degrades safely to `null` on invalid tokens.
- Impact: Medium to High. Improves frontend auth resilience and reduces chance of tenant context misuse.

Validation notes:
- Expected behavior: valid JWT continues to resolve tenant/session key; malformed/non-JWT token returns `null` and avoids unsafe fallbacks.
- Follow-up validation: verify login flow, tenant-scoped cache behavior, and error handling with corrupted token input.

### Next Planned Step

- Harden [backend/app/config.py](backend/app/config.py) by removing insecure default secrets and enforcing required env values outside development.

