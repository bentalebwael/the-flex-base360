#!/usr/bin/env bash
set -euo pipefail

BACKEND_CONTAINER="new_devs_app-backend-1"

echo "Running tenant resolver unknown-user fallback check..."

RESULT=$(
  docker exec -i "${BACKEND_CONTAINER}" python - <<'PY'
import asyncio
from app.core.tenant_resolver import TenantResolver

async def main():
    tenant_id = await TenantResolver.resolve_tenant_id(
        user_id="unknown-user",
        user_email="unknown@example.com",
        token=None,
    )
    print(tenant_id)

asyncio.run(main())
PY
)

echo
echo "=== Evidence ==="
echo "Resolved tenant for unknown user: ${RESULT}"

echo
echo "=== Conclusion ==="
if [[ "${RESULT}" == "tenant-a" ]]; then
  echo "❌ BUG CONFIRMED: unknown user falls back to tenant-a"
  echo "- Tenant resolution is fail-open"
  echo "- This can incorrectly assign an unaffiliated user to tenant-a"
  echo "- That may cause tenant isolation and authorization issues"
else
  echo "✅ PASS: unknown user does not default to tenant-a"
  echo "- Tenant resolution appears to fail closed"
fi