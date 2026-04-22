#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="http://localhost:8000"
BACKEND_CONTAINER="new_devs_app-backend-1"
REDIS_CONTAINER="new_devs_app-redis-1"
DB_CONTAINER="new_devs_app-db-1"

PROPERTY_ID="prop-001"
TENANT_ID="tenant-a"

TENANT_A_EMAIL="sunset@propertyflow.com"
TENANT_A_PASSWORD="client_a_2024"

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
    "revenue:${TENANT_ID}:${PROPERTY_ID}" >/dev/null
}

db_all_time_total() {
  docker exec -i "${DB_CONTAINER}" psql -U postgres -d propertyflow -t -A -F ' | ' -c "
SELECT SUM(total_amount), COUNT(*)
FROM reservations
WHERE tenant_id = '${TENANT_ID}'
  AND property_id = '${PROPERTY_ID}';
" | tr -d '[:space:]'
}

backend_error_logs() {
  docker logs "${BACKEND_CONTAINER}" 2>&1 | tail -n 200 | grep -E "Database error|Database pool initialization failed" || true
}

echo "Running dashboard revenue source verification..."

TOKEN_A=$(login "${TENANT_A_EMAIL}" "${TENANT_A_PASSWORD}")

clear_keys

API_RESPONSE=$(call_summary "${TOKEN_A}")
REDIS_TENANT_KEY=$(redis_get "revenue:${TENANT_ID}:${PROPERTY_ID}")
REDIS_LEGACY_KEY=$(redis_get "revenue:${PROPERTY_ID}")
DB_TOTAL=$(db_all_time_total)
BACKEND_LOGS=$(backend_error_logs)

echo
echo "=== Evidence ==="
echo "API response: ${API_RESPONSE}"
echo "Redis tenant-aware key: ${REDIS_TENANT_KEY:-<empty>}"
echo "Redis legacy key: ${REDIS_LEGACY_KEY:-<empty>}"
echo "DB all-time total (sum | count): ${DB_TOTAL:-<empty>}"

echo
echo "Backend log check:"
if [[ -n "${BACKEND_LOGS}" ]]; then
  echo "${BACKEND_LOGS}"
else
  echo "<no matching DB failure logs>"
fi

echo
echo "=== Conclusion ==="

if [[ -n "${BACKEND_LOGS}" ]]; then
  echo "❌ BUG CONFIRMED: Dashboard is using fallback/mock revenue instead of real DB data"
  echo "- Backend shows database initialization/query failure"
  echo "- API response should not be trusted as source-of-truth revenue"
  echo "- Redis may be caching fallback/mock results"
else
  echo "✅ DB path appears available"
  echo "- No DB failure log detected in recent backend output"
  echo "- Compare API response against DB totals to verify whether revenue logic is correct"
fi