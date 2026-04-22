#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="http://localhost:8000"
REDIS_CONTAINER="new_devs_app-redis-1"
PROPERTY_ID="prop-001"

TENANT_A_EMAIL="sunset@propertyflow.com"
TENANT_A_PASSWORD="client_a_2024"

TENANT_B_EMAIL="ocean@propertyflow.com"
TENANT_B_PASSWORD="client_b_2024"

login() {
  curl -s -X POST "${BACKEND_URL}/api/v1/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$1\",\"password\":\"$2\"}" \
  | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])'
}

call_summary() {
  curl -s "${BACKEND_URL}/api/v1/dashboard/summary?property_id=${PROPERTY_ID}" \
    -H "Authorization: Bearer $1"
}

redis_get() {
  docker exec -i "${REDIS_CONTAINER}" redis-cli GET "$1" 2>/dev/null || true
}

clear_keys() {
  docker exec -i "${REDIS_CONTAINER}" redis-cli DEL \
    "revenue:${PROPERTY_ID}" \
    "revenue:tenant-a:${PROPERTY_ID}" \
    "revenue:tenant-b:${PROPERTY_ID}" >/dev/null
}

echo "Running cache isolation verification..."

TOKEN_A=$(login "${TENANT_A_EMAIL}" "${TENANT_A_PASSWORD}")
TOKEN_B=$(login "${TENANT_B_EMAIL}" "${TENANT_B_PASSWORD}")

# --- Test 1: A -> B ---
clear_keys

RESP_A=$(call_summary "${TOKEN_A}")
RESP_B=$(call_summary "${TOKEN_B}")

LEGACY_KEY_1=$(redis_get "revenue:${PROPERTY_ID}")

# --- Test 2: B -> A ---
clear_keys

RESP_B_REV=$(call_summary "${TOKEN_B}")
RESP_A_REV=$(call_summary "${TOKEN_A}")

LEGACY_KEY_2=$(redis_get "revenue:${PROPERTY_ID}")

echo
echo "=== Evidence ==="
echo "Tenant A response (A -> B): $RESP_A"
echo "Tenant B response (A -> B): $RESP_B"
echo "Tenant B response (B -> A): $RESP_B_REV"
echo "Tenant A response (B -> A): $RESP_A_REV"

echo
echo "Redis key used:"
echo "revenue:${PROPERTY_ID} => ${LEGACY_KEY_2:-<empty>}"

echo
echo "=== Conclusion ==="

if [[ -n "${LEGACY_KEY_1}" || -n "${LEGACY_KEY_2}" ]]; then
  echo "❌ BUG CONFIRMED: Cross-tenant cache collision detected"
  echo "- Shared Redis key (revenue:${PROPERTY_ID}) is used"
  echo "- Cache value depends on request order"
  echo "- This can expose one tenant's data to another"
else
  echo "✅ FIXED: Cache is tenant-isolated"
  echo "- No shared Redis key detected"
  echo "- Tenant-aware keys are expected to be used"
fi