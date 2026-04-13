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

### 2026-04-13 - Step 5 Completed

Change made:
- Updated [backend/app/config.py](backend/app/config.py) with production-like environment validation for secret configuration.
- Added explicit validation to fail startup if `SECRET_KEY` or `TOKEN_ENCRYPTION_KEY` are unset or still using insecure defaults in `production` or `staging`.
- Reduced sensitive startup log exposure by logging only SET/NOT SET status and length instead of secret previews.

Why this change:
- Insecure defaults are acceptable only for local challenge/development scenarios, not for deployable environments.
- Startup-time validation is the safest control because it prevents accidental insecure deployments from booting.
- Removing secret previews from logs reduces credential exposure risk in log aggregation systems.

Risk and impact assessment:
- Risk: Medium. Misconfigured staging/production environments will now fail fast at startup (intended behavior).
- Impact: High. Significantly improves deployment security posture and reduces chance of credential leakage.

Validation notes:
- Expected behavior: development environment still boots with defaults; staging/production requires explicit secure secret values.
- Follow-up validation: run startup with `environment=production` and verify missing/default secrets stop boot; verify valid secrets allow normal startup.

### 2026-04-13 - Step 6 Completed

Change made:
- Added focused backend tests in [backend/tests/test_dashboard_tenant_isolation.py](backend/tests/test_dashboard_tenant_isolation.py).
- Test 1 verifies dashboard summary uses authenticated tenant context when invoking revenue summary.
- Test 2 verifies missing tenant context returns HTTP 401 and does not call revenue summary logic.

Why this change:
- Tenant isolation controls are high-risk and require regression coverage after Step 1 and Step 2 behavior changes.
- These tests validate both positive path (tenant-scoped execution) and fail-closed path (missing tenant rejection).
- Fast, focused tests increase confidence while keeping maintenance overhead low.

Risk and impact assessment:
- Risk: Low. Test-only change.
- Impact: Medium to High. Adds guardrails against regression in tenant boundary enforcement.

Validation notes:
- Expected behavior: tests pass with tenant-aware dashboard route and fail if fallback behavior is reintroduced.
- Follow-up validation: run pytest for this module in CI and gate merges touching dashboard/auth cache paths.

### 2026-04-13 - Step 7 Completed

Change made:
- Fixed local test runner setup by creating backend virtual environment at `backend/.venv` and installing project dependencies plus `pytest`.
- Updated [backend/pyproject.toml](backend/pyproject.toml) to include `pytest` in the `dev` dependency group.

Why this change:
- Team velocity depends on reliable local test execution; missing pytest blocked validation and slowed iteration.
- Adding pytest to managed dev dependencies prevents recurring setup drift on fresh environments.

Risk and impact assessment:
- Risk: Low. Tooling/development-only change.
- Impact: High. Restores ability to run backend regression tests quickly and consistently.

Validation notes:
- Command run: `.venv\\Scripts\\python.exe -m pytest tests/test_dashboard_tenant_isolation.py -q`
- Result: `2 passed`.

### 2026-04-13 - Step 8 Completed

Change made:
- Updated [.github/workflows/ci.yml](.github/workflows/ci.yml) to add a dedicated `backend-tests` job on pull requests to `main`.
- New CI job sets up Python 3.12, installs backend dependencies, and runs `python -m pytest -q` in `backend/`.

Why this change:
- Tenant-isolation regression tests only reduce risk if they are enforced automatically at merge time.
- CI enforcement shifts failure detection left and prevents silent regressions from reaching staging/production.

Risk and impact assessment:
- Risk: Low to Medium. CI duration increases slightly and may expose pre-existing test/environment issues.
- Impact: High. Converts local-only testing into a merge gate for backend correctness and tenant-boundary safety.

Validation notes:
- Workflow syntax updated and scoped to pull request checks.
- Local baseline remains green for tenant isolation tests (`2 passed`).

### 2026-04-13 - Step 9 Completed

Change made:
- Updated [frontend/package.json](frontend/package.json) to add a dedicated `type-check` script (`tsc -b`).
- Updated [.github/workflows/ci.yml](.github/workflows/ci.yml) to add a `frontend-quality` pull-request job.
- New frontend CI job installs frontend dependencies, runs `npm run lint`, and runs `npm run type-check`.

Why this change:
- Backend test gating alone leaves frontend regressions (type errors and lint regressions) undetected until later stages.
- Enforcing lint and type checks on pull requests creates a balanced quality gate across both application layers.

Risk and impact assessment:
- Risk: Medium. Existing frontend lint/type debt may initially fail PRs until remediated.
- Impact: High. Prevents low-level frontend defects from merging and improves release predictability.

Validation notes:
- Workflow and package script definitions updated for automated frontend quality checks.
- Follow-up validation: execute frontend lint and type-check locally and in CI to baseline current debt.

### Next Planned Step

- Triage and fix current frontend lint/type failures (if any) so the new `frontend-quality` gate remains stable and actionable.

