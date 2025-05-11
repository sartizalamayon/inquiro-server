#!/usr/bin/env bash
# Usage: bash test_analytics_api.sh sartizayo.on@gmail.com
set -e

BASE_URL="http://localhost:8000"   # FastAPI port
USER_EMAIL="$1"
[[ -z "$USER_EMAIL" ]] && { echo "provide email arg"; exit 1; }

echo "GET metrics …"
curl -s "$BASE_URL/analytics/metrics/$USER_EMAIL" | jq .

echo "GET insights …"
curl -s "$BASE_URL/analytics/insights/$USER_EMAIL" | jq .
